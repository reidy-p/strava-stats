[Strava](https://www.strava.com) is a popular social network where runners and cyclists can upload and compare data from their activities. However, athletic performance can be significantly affected by weather conditions such as temperature, wind, and humidity and this data is typically not available on Strava. This project allows a user to download their own running data from Strava's API and to combine it with weather data from the [DarkSky API](https://www.darksky.net/dev/) to adjust for weather conditions.

This project is still under active development.

Features
---

Usage
---


TODO
---
* Improved location data using latitude and longitude and Google maps API
* Try to predict fitness at certain points of time (vdot based on races)
* Command line arguments
* Adjusting pacing depending on wind (maybe too hard because of direction)
* Use richer python types for quantities rather than the simple string or numeric values that the Strava API returns or the simple quantities that stravalib returns
* Grouping similar activities. Is this done already or is it something I could do?
