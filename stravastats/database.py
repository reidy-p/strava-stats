from datetime import datetime
from datetime import datetime
from stravastats import db, app

def get_latest_activity_date(): 
    latest_activity_date = db.session.query(db.func.max(Activity.start_date_utc)).scalar()
    app.logger.info(f"Latest activity date found: {latest_activity_date}")
    return latest_activity_date

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    workout_type = db.Column(db.String, nullable=False)
    start_date_utc = db.Column(db.DateTime, nullable=False)
    moving_time = db.Column(db.String, nullable=False)
    moving_time_seconds = db.Column(db.Integer, nullable=False)
    total_elevation_gain_metres = db.Column(db.Float, nullable=False)
    distance_metres = db.Column(db.Float, nullable=False)
    location_city = db.Column(db.String, nullable=True)
    location_country = db.Column(db.String, nullable=False)
    start_latitude = db.Column(db.Float, nullable=False)
    start_longitude = db.Column(db.Float, nullable=False)
    weather_summary = db.Column(db.String, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    dew_point = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    wind_gust = db.Column(db.Float, nullable=False)
    hadley_score = db.Column(db.Float, nullable=False)
    minutes_per_km = db.Column(db.Float, nullable=False)
    minutes_per_km_adjusted = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Activity('{self.name}', '{self.start_date_utc}')"

