from datetime import datetime

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
