import requests

def calculate_vdot(distance_metres, seconds):
    """
    Calculate VDOT using the runsmartproject calculator. There is no public
    API for this calculator so I reverse engineered how the POST request
    seems to work to get the VDOT calculations and equivalent race results 
    """

    # hours
    hours = seconds // 3600 
    # remaining seconds
    remaining_seconds = seconds - (hours * 3600)
    # minutes
    minutes = remaining_seconds // 60
    # remaining seconds
    seconds = remaining_seconds - (minutes * 60)
    
    request_data = {
      'distance': round(distance_metres, -3) / 1000,
      'unit': 'km',
      'time': '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    }
    
    vdot_data = requests.post('https://runsmartproject.com/vdot/app/api/find_paces', 
                              data=request_data)
    return vdot_data.json()['vdot']
 

