from flask import Flask, render_template, url_for
from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
import sqlite3
from utils import calculate_vdot
import datetime
app = Flask(__name__)


@app.route("/")
def home():
   return render_template('home.html') 

@app.route("/adjustedpaces")
def adjusted_paces():
    conn = sqlite3.connect('activities.db')
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

@app.route("/anomalies")
def anomalies():
    conn = sqlite3.connect('activities.db')
    with conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, workout_type, distance_metres, total_elevation_gain_metres, minutes_per_km, minutes_per_km_adjusted, temperature, humidity 
            FROM activities 
        """)
        activities = pd.DataFrame([dict(row) for row in cursor.fetchall()])
    
    clf = LocalOutlierFactor()
    y_pred = clf.fit_predict(activities[['distance_metres', 'total_elevation_gain_metres', 'minutes_per_km', 'minutes_per_km_adjusted', 'temperature', 'humidity']])
    anomalies = activities[y_pred == -1]
    return render_template('anomalies.html', posts=anomalies.to_dict(orient='records'))

@app.route("/vdot")
def vdot():
    conn = sqlite3.connect('activities.db')
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

if __name__ == '__main__':
    app.run(debug=True)
