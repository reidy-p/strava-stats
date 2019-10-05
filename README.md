# Strava Stats

This project is under active development.

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

This project uses [Redis](https://redis.io/) to track the progress of the downloading of data from the Strava API. To download data you must have redis installed and the Redis server running. You can download Redis from the website and start the server by running:
```
$ ./redis-stable/src/redis-server
```

To start the flask app run:
```
$ python run.py
```

Go to ``localhost:5000`` on your web browser

DarkSky API
---
This app uses the [DarkSky API](https://darksky.net/dev) to gather historical weather data. You will need to sign up to the API to get a key to put in the ``config.yml`` file as shown above. Note that you can get 1,000 API calls for free each day from the DarkSky API. You must pay for additional calls beyond this limit by signing up on the API's website.
