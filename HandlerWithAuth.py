import http.server
from urllib.parse import parse_qs
import requests
import logging
import sys
import sqlite3
from datetime import datetime
from utils import calculate_speed, calculate_hadley_score, format_seconds


class HandlerWithAuth(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        client = self.server.client
        secret_keys = self.server.secret_keys
        parsed_qs = parse_qs(self.path)
        if 'code' in parsed_qs:
            self.send_response(200)
            self.send_header('Content-type', "text/html")
            self.end_headers()
            self.wfile.write(bytes(open("templates/authorized.html").read(), "UTF-8"))

            token_response = client.exchange_code_for_token(client_id=secret_keys['client_id'], client_secret=secret_keys['client_secret'], code=parsed_qs['code'])

            conn = sqlite3.connect('activities.db')
            with conn:
                cursor = conn.cursor()
                create_table_if_not_exists(cursor)
                latest_activity_date = get_latest_activity_date(cursor)

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

                        # Will there be duplicate rows?
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

        else:
            self.send_response(401)
            self.send_header('Content-type', "text/html")
            self.end_headers()
            self.wfile.write(bytes(open("templates/notauthorized.html").read(), "UTF-8"))




def make_darksky_request(api_key, latitude, longitude, time):
    # Dark Sky API can't handle microseconds
    clean_time = time.replace(microsecond=0)
    url = "https://api.darksky.net/forecast/{}/{},{}".format(api_key, latitude, longitude, clean_time)
    return requests.get(url)

def get_latest_activity_date(cursor):
    cursor.execute("""SELECT MAX(start_date_unix) FROM activities""")
    latest_activity_date = cursor.fetchone()[0]
    if latest_activity_date is None:
        return None
    else:
        print("latest activity date is", datetime.fromtimestamp(latest_activity_date))
        return datetime.fromtimestamp(latest_activity_date)

def create_table_if_not_exists(cursor):
    sql_create_table = """CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        workout_type TEXT NOT NULL,
        start_date_unix INTEGER NOT NULL,
        moving_time TEXT NOT NULL,
        moving_time_seconds INTEGER NOT NULL,
        type TEXT NOT NULL,
        total_elevation_gain_metres REAL NOT NULL,
        distance_metres REAL NOT NULL,
        location_city TEXT,
        location_country TEXT NOT NULL,
        start_latitude REAL NOT NULL,
        start_longitude REAL NOT NULL,
        weather_summary TEXT NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        dew_point REAL NOT NULL,
        wind_speed REAL NOT NULL,
        wind_gust REAL NOT NULL,
        hadley_score REAL NOT NULL,
        minutes_per_km REAL NOT NULL,
        minutes_per_km_adjusted REAL NOT NULL
    );
    """
    cursor.execute(sql_create_table)


