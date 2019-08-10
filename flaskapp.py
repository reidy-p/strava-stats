from flask import Flask, render_template, url_for
import sqlite3
app = Flask(__name__)

conn = sqlite3.connect('activities.db')
with conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, minutes_per_km, minutes_per_km_adjusted, weather_summary, temperature, humidity 
        FROM activities 
        ORDER BY hadley_score DESC 
        LIMIT 10
    """)
    posts = []
    for row in cursor.fetchall():
        posts.append({
            'name': row[0],
            'minutes_per_km': row[1],
            'minutes_per_km_adjusted': row[2],
            'summary': row[3],
            'temperature': row[4],
            'humidity': row[5]
        })


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


if __name__ == '__main__':
    app.run(debug=True)
