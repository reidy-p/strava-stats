import requests
from pint import UnitRegistry
from stravastats import app
import math

def format_seconds(seconds):
    """
    Create a string of HH:MM:SS from seconds
    """

    # hours
    hours = seconds // 3600 
    # remaining seconds
    remaining_seconds = seconds - (hours * 3600)
    # minutes
    minutes = remaining_seconds // 60
    # remaining seconds
    seconds = remaining_seconds - (minutes * 60)

    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

def calculate_vdot(distance_metres, moving_time):
    """
    Calculate VDOT using the runsmartproject calculator. There is no public
    API for this calculator so I reverse engineered how the POST request
    seems to work to get the VDOT calculations and equivalent race results 
    """

    request_data = {
      'distance': round(distance_metres, -2) / 1000,
      'unit': 'km',
      'time': moving_time
    }
    
    vdot_data = requests.post('https://runsmartproject.com/vdot/app/api/find_paces', 
                              data=request_data)

    return (vdot_data.json()['vdot'], vdot_data.json()['paces']['equivs'])

def calculate_speed(moving_time_seconds, distance_metres):
    ureg = UnitRegistry()
    moving_minutes = (moving_time_seconds * ureg.seconds).to(ureg.minutes)
    km = (distance_metres * ureg.meters).to(ureg.kilometers)

    return moving_minutes / km

def calculate_hadley_score(dewPoint, temperature):
    if dewPoint is None or temperature is None:
        return (None, None)

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

def make_darksky_request(api_key, latitude, longitude, time):
    # Dark Sky API can't handle microseconds
    clean_time = time.replace(microsecond=0)
    url = "https://api.darksky.net/forecast/{}/{},{}".format(api_key, latitude, longitude, clean_time)
    return requests.get(url)

def format_pace(minutes_per_km):
    (frac, integer) = math.modf(minutes_per_km)
    seconds = round(frac*60, 0)
    if seconds >= 60:
        integer += 1
        seconds = 0
    return f"{integer:.0f}:{seconds:02.0f}"

