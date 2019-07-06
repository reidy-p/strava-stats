from stravalib.client import Client
import webbrowser
import http.server
import socketserver
from urllib.parse import parse_qs
import csv
import requests
from pint import UnitRegistry
import logging
import yaml
import sys


class HandlerWithAuth(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_qs = parse_qs(self.path)
        if 'code' in parsed_qs:
            self.send_response(200)
            self.send_header('Content-type', "text/html")
            self.end_headers()
            self.wfile.write(bytes(open("authorized.html").read(), "UTF-8"))

            token_response = client.exchange_code_for_token(client_id=secret_keys['client_id'], client_secret=secret_keys['client_secret'], code=parsed_qs['code'])
            activities = client.get_activities()

            with open('activities.csv', 'w', newline='') as csvfile:
                activity_writer = csv.writer(csvfile, delimiter=',')
                cols = ['upload_id', 'start_date', 'start_date_local', 'moving_time', 'type', 'total_elevation_gain', 'average_speed', 'distance', 'location_city', 
                        'location_country', 'start_latitude', 'start_longitude', 'summary', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'hadley_score',
                        'minutes_per_km', 'minutes_per_km_adjusted', 'pace_discrepancy']
                activity_writer.writerow(cols)
                ureg = UnitRegistry()

                logger = logging.getLogger()
                logger.setLevel('ERROR')

                for activity in activities:
                    request = make_darksky_request(activity.start_latitude, activity.start_longitude, activity.start_date_local)

                    if request.status_code == 200:
                        weather_data = request.json()['currently']

                        moving_minutes = (activity.moving_time.total_seconds() * ureg.seconds).to(ureg.minutes)
                        km = (activity.distance.get_num() * ureg.meters).to(ureg.kilometers)
                        minutes_per_km = moving_minutes / km

                        (hadley_score, hadley_pace_adjustment) = calculate_hadley_score(weather_data['dewPoint'], weather_data['temperature'])
                        minutes_per_km_hadley_adjusted = minutes_per_km * (1 - hadley_pace_adjustment)

                        activity_writer.writerow([
                            activity.upload_id,
                            activity.start_date,
                            activity.start_date_local,
                            activity.moving_time,
                            activity.type,
                            activity.total_elevation_gain,
                            activity.average_speed,
                            activity.distance,
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
                            minutes_per_km,
                            minutes_per_km_hadley_adjusted,
                            abs(minutes_per_km - minutes_per_km_hadley_adjusted)
                        ])
                    elif request.status_code == 400:
                        print("{} Error: {}".format(request.json()['code'], request.json()['error']))
                        print("Skipping request and continuing to next activity")
                    else:
                        print("{} Error: {}".format(request.json()['code'], request.json()['error']))
                        print("Terminating")
                        break

        else:
            self.send_response(401)
            self.send_header('Content-type', "text/html")
            self.end_headers()
            self.wfile.write(bytes(open("notauthorized.html").read(), "UTF-8"))


class TCPServerWithReusableAddress(socketserver.TCPServer):
    # Allow the server to reuse an address. The default of False 
    # means that stopping and then restarting the server in quick 
    # succession leads to an error
    allow_reuse_address = True

def make_darksky_request(latitude, longitude, time):
    # Dark Sky API can't handle microseconds
    clean_time = time.replace(microsecond=0)
    url = "https://api.darksky.net/forecast/{}/{},{}".format(secret_keys['darksky_api_key'], latitude, longitude, clean_time)
    return requests.get(url)

def calculate_hadley_score(dewPoint, temperature):
    hadley_score = dewPoint + temperature

    if hadley_score <= 100:
        adjustment = 0
    elif hadley_score <= 110:
        adjustment = 0.005
    elif hadley_score <= 120:
        adjustment = 0.01
    elif hadley_score <= 130:
        adjustment = 0.02
    elif hadley_score <= 140:
        adjustment = 0.03
    elif hadley_score <= 150:
        adjustment = 0.045
    elif hadley_score <= 160:
        adjustment = 0.06
    elif hadley_score <= 170:
        adjustment = 0.08
    elif hadley_score <= 180:
        adjustment = 0.10
    else:
        adjustment = 0

    return (hadley_score, adjustment)

if len(sys.argv) < 2:
    print("You must pass command line arguments")

elif sys.argv[1] == "create_data":

    with open("keys.yml", 'r') as keys_file:
        secret_keys = yaml.safe_load(keys_file)
    
    client = Client()
    authorize_url = client.authorization_url(
        client_id=secret_keys['client_id'], 
        redirect_uri='http://127.0.0.1:5000/authorized'
    )
    
    # Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
    webbrowser.open(authorize_url)
    
    with TCPServerWithReusableAddress(("127.0.0.1", 5000), HandlerWithAuth) as httpd:
        print("serving at port", 5000)
        httpd.handle_request()
        print("shutting down server")
    
else:
    pass
