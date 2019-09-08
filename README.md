# Strava Stats

This project is still under active development.

[Strava](https://www.strava.com) is a popular social network where runners and cyclists can upload and compare data from their activities. This project allows a user to download their own running data from Strava's API and to calculate and view additional statistics. It is inspired by the [Strava Wind Analysis](https://github.com/MathBunny/strava-wind-analysis) for cyclists.

Features
---
* Strava OAuth authentication
* Calculate adjusted running paces that take account of temperature and humidity using historical weather data from the [DarkSky API](https://darksky.net/dev)
* Calculate VDOT based on race performances and view estimates of equivalent race results
* Detect anomalous activities

Screenshots
---

Usage
---
Setup the configuration file (``config.yml``) as follows:
```yaml
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
darksky_api_key: YOUR_DARKSKY_API_KEY
redis_port: 6379
redis_password: YOUR_REDIS_PASSWORD
```

To start the flask app run:
```
$ python run.py
```

Go to ``localhost:5000`` on your web browser


TODO
---
* Improved logging
* Use SQLAlchemy?
* Improved anomaly detection
* Package structure
* Adjusting pacing depending on wind (maybe too hard because of direction)
* Improved location data using latitude and longitude and Google maps API
* Grouping similar activities. Is this done already or is it something I could do?
* Use richer python types for quantities rather than the simple string or numeric values that the Strava API returns or the simple quantities that stravalib returns
