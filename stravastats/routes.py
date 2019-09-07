import pandas as pd
import requests
from sklearn.neighbors import LocalOutlierFactor
from flask import render_template, url_for, redirect, request, send_file, Response
import sqlite3
from stravastats.utils import calculate_vdot
from stravastats import app, executor
import yaml
import logging
import redis
from stravalib.client import Client
from stravastats.utils import calculate_speed, calculate_hadley_score, format_seconds, make_darksky_request
from stravastats.database import create_table_if_not_exists, get_latest_activity_date
import time

with open("config.yml", 'r') as keys_file:
    config = yaml.safe_load(keys_file)

r = redis.StrictRedis(host="localhost", port=config['redis_port'], password=config['redis_password'], decode_responses=True)

@app.route("/")
def login():
    c = Client()
    url = c.authorization_url(client_id=config['client_id'],
                              redirect_uri=url_for('.logged_in', _external=True),
                              approval_prompt='auto',
                              # Change to None if you don't want private activities included
                              scope='activity:read_all'
    )

    return render_template('login.html', authorize_url=url)

@app.route("/strava-oauth")
def logged_in():
    """
    Method called by Strava (redirect) that includes parameters.
    - state
    - code
    - error
    """

    error = request.args.get('error')
    state = request.args.get('state')
    if error:
        return render_template('login_error.html', error=error)
    else:
        code = request.args.get('code')

        return render_template('login_success.html', code=code)

@app.route("/stravastats")
def stravastats():
   return render_template('stravastats.html') 

@app.route("/adjustedpaces")
def adjusted_paces():
    conn = sqlite3.connect('stravastats/activities.db')
    with conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, workout_type, minutes_per_km, minutes_per_km_adjusted, weather_summary, temperature, humidity 
            FROM activities 
            ORDER BY hadley_score DESC 
            LIMIT 10
        """)
    posts = [dict(row) for row in cursor.fetchall()]
    return render_template('adjusted_paces.html', posts=posts)

@app.route("/anomalies")
def anomalies():
    conn = sqlite3.connect('stravastats/activities.db')
    with conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, workout_type, distance_metres, moving_time, moving_time_seconds, total_elevation_gain_metres, minutes_per_km, minutes_per_km_adjusted, temperature, humidity 
            FROM activities 
        """)
        activities = pd.DataFrame([dict(row) for row in cursor.fetchall()])
    
    clf = LocalOutlierFactor()
    y_pred = clf.fit_predict(activities[['distance_metres', 'moving_time_seconds', 'total_elevation_gain_metres', 'minutes_per_km', 'minutes_per_km_adjusted', 'temperature', 'humidity']])
    anomalies = activities[y_pred == -1]
    return render_template('anomalies.html', posts=anomalies.to_dict(orient='records'))

@app.route("/vdot")
def vdot():
    conn = sqlite3.connect('stravastats/activities.db')
    with conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, distance_metres, moving_time, minutes_per_km 
            FROM activities 
            WHERE workout_type='Race'
        """)
        races = pd.DataFrame([dict(row) for row in cursor.fetchall()])
    
    posts = []
    for r in races.to_dict(orient='records'):
        (r['vdot'], r['equivs']) = calculate_vdot(r['distance_metres'], r['moving_time'])
        posts.append(r)
    
    return render_template('races.html', posts=posts)

@app.errorhandler(sqlite3.OperationalError)
def handle_no_table(error):
    if str(error) == "no such table: activities":
        return render_template('noactivitydata.html')
    else:
        return render_template('sqliteerror.html', error=error)

@app.route('/progressbar')
def progress_bar():
    return send_file('templates/progressbar.html')

@app.route('/progress')
def progress():
  """Get percentage progress for auto attribute process"""
  #r.set("progress", str(0))
  def progress_stream():
    p = r.get("progress")
    p_msg = "data:" + str(p) + "\n\n"
    yield p_msg
    time.sleep(5)
    #while p < 100:
      #p = int(r.get("progress"))
      #yield p_msg
      # Client closes EventSource on 100%, gets reopened when `submit` is pressed
      #if p == 100:
      #  r.set("progress", str(0))
      #time.sleep(1)

  return Response(progress_stream(), mimetype='text/event-stream')

def download_task(code):

    conn = sqlite3.connect('stravastats/activities.db')
    with conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        latest_activity_date = get_latest_activity_date(cursor)

    client = Client()
    access_token = client.exchange_code_for_token(client_id=config['client_id'],
                                                  client_secret=config['client_secret'],
                                                  code=code)
    
    # Only get new activities to avoid rate limits
    activities = client.get_activities(after=latest_activity_date)
    
    logger = logging.getLogger()
    logger.setLevel('INFO')

    num_activities = len(list(activities))
    app.logger.info(f"{num_activities} activities found")
    for counter, activity in enumerate(activities):
        darksky_request = make_darksky_request(config['darksky_api_key'], activity.start_latitude, activity.start_longitude, activity.start_date_local)

        progress_pct = ((counter + 1) / num_activities) * 100
        r.set("progress", str(progress_pct))
    
        if darksky_request.status_code == 200:
            weather_data = darksky_request.json()['currently']
    
            with conn:
                c = conn.cursor()
    
                (hadley_score, hadley_pace_adjustment) = calculate_hadley_score(weather_data['dewPoint'], weather_data['temperature'])
                minutes_per_km = calculate_speed(activity.moving_time.total_seconds(), activity.distance.get_num())
                minutes_per_km_hadley_adjusted = minutes_per_km * (1 - hadley_pace_adjustment)
    
                activity_link = "https://www.strava.com/activities/" + str(activity.id)
    
                workout_types_lookup = {
                    '0': 'Easy Run',
                    '1': 'Race',
                    '2': 'Long Run',
                    '3': 'Workout'
                }

                row = (
                    activity.id,
                    activity.name,
                    workout_types_lookup.get(activity.workout_type, 'N/A'),
                    activity.start_date.timestamp(),
                    format_seconds(activity.moving_time.total_seconds()),
                    activity.moving_time.total_seconds(),
                    activity.type,
                    activity.total_elevation_gain.get_num(),
                    activity.distance.get_num(),
                    activity.location_city,
                    activity.location_country,
                    activity.start_latitude,
                    activity.start_longitude,
                    weather_data['summary'],
                    weather_data['temperature'],
                    weather_data['humidity'],
                    weather_data['dewPoint'],
                    weather_data['windSpeed'],
                    weather_data['windGust'],
                    hadley_score,
                    minutes_per_km.magnitude,
                    minutes_per_km_hadley_adjusted.magnitude
                )
    
                # Avoid SQL injection
                c.execute("""INSERT OR IGNORE INTO activities
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", row)

        elif darksky_request.status_code == 400:
            error_msg = f"{darksky_request.json()['code']} Error: {darksky_request.json()['error']}"
            app.logger.warn(error_msg + ", skipping request and continuing to next activity")
        elif darksky_request.status_code == 403:
            app.logger.error(f"{darksky_request.json()['code']} Error: DarkSky API daily usage limit exceeded. Terminating data download")
            break
        else:
            app.logger.error(f"{darksky_request.json()['code']} Error: {darksky_request.json()['error']}. Terminating data download")
            break

@app.route('/download/<code>')
def run_download_multithread(code):
    r.set("progress", str(0))
    executor.submit(download_task, code)
    return redirect(url_for('progress_bar'))

