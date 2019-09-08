from flask import Flask
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
executor = Executor(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activities.db'
db = SQLAlchemy(app)

from stravastats import routes
