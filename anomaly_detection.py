from sklearn.neighbors import LocalOutlierFactor
import sqlite3
import numpy as np

clf = LocalOutlierFactor()

conn = sqlite3.connect('activities.db')
with conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, distance_metres, total_elevation_gain_metres, minutes_per_km, minutes_per_km_adjusted, temperature, humidity 
        FROM activities 
    """)
    result = [dict(row) for row in cursor.fetchall()]

X = [(r['distance_metres'], r['total_elevation_gain_metres'], r['minutes_per_km'], r['minutes_per_km_adjusted'], r['temperature'], r['humidity']) for r in result]

y_pred = clf.fit_predict(X)
print(y_pred)
#print(X[y_pred == -1])

