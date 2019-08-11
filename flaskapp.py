from flask import Flask, render_template, url_for
import sqlite3
app = Flask(__name__)

conn = sqlite3.connect('activities.db')
with conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, minutes_per_km, minutes_per_km_adjusted, weather_summary, temperature, humidity 
        FROM activities 
        ORDER BY hadley_score DESC 
        LIMIT 10
    """)
    posts = [dict(row) for row in cursor.fetchall()]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


if __name__ == '__main__':
    app.run(debug=True)
