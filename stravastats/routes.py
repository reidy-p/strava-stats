import pandas as pd
import requests
from sklearn.neighbors import LocalOutlierFactor
from flask import render_template, url_for, redirect, request
import sqlite3
from stravastats.utils import calculate_vdot
from stravastats import app
import yaml
import logging
from stravalib.client import Client
from stravastats.utils import calculate_speed, calculate_hadley_score, format_seconds
from stravastats.database import create_table_if_not_exists, get_latest_activity_date


@app.route("/")
def login():
    with open("config.yml", 'r') as keys_file:
        secret_keys = yaml.safe_load(keys_file)

    c = Client()
    url = c.authorization_url(client_id=secret_keys['client_id'],
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

    with open("config.yml", 'r') as keys_file:
        secret_keys = yaml.safe_load(keys_file)

    error = request.args.get('error')
    state = request.args.get('state')
    if error:
        return render_template('login_error.html', error=error)
    else:
        code = request.args.get('code')

        return render_template('login_success.html', code=code)

@app.route("/download/<code>")
def download_data(code):

    with open("config.yml", 'r') as keys_file:
        secret_keys = yaml.safe_load(keys_file)

    conn = sqlite3.connect('stravastats/activities.db')
    with conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        latest_activity_date = get_latest_activity_date(cursor)

    client = Client()
    access_token = client.exchange_code_for_token(client_id=secret_keys['client_id'],
                                                  client_secret=secret_keys['client_secret'],
                                                  code=code)
    
    # Only get new activities to avoid rate limits
    activities = client.get_activities(after=latest_activity_date)
    
    logger = logging.getLogger()
    logger.setLevel('ERROR')
    
    for activity in activities:
        darksky_request = make_darksky_request(secret_keys['darksky_api_key'], activity.start_latitude, activity.start_longitude, activity.start_date_local)
    
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
            error_msg = "{} Error: {}".format(darksky_request.json()['code'], darksky_request.json()['error'])
            print(error_msg + ", skipping request and continuing to next activity")
        elif darksky_request.status_code == 403:
            print("{} Error: DarkSky API daily usage limit exceeded".format(darksky_request.json()['code']))
            print("Terminating")
            break
        else:
            print("{} Error: {}".format(darksky_request.json()['code'], darksky_request.json()['error']))
            print("Terminating")
            break
        
    return redirect(url_for('home'))

@app.route("/stravastats")
def stravastats():
   return render_template('stravastats.html') 

@app.route("/adjustedpaces")
def adjusted_paces():
    try:
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
    except sqlite3.OperationalError as e:
        if str(e) == "no such table: activities":
            return render_template('noactivitydata.html')
        else:
            raise

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

def make_darksky_request(api_key, latitude, longitude, time):
    # Dark Sky API can't handle microseconds
    clean_time = time.replace(microsecond=0)
    url = "https://api.darksky.net/forecast/{}/{},{}".format(api_key, latitude, longitude, clean_time)
    return requests.get(url)

