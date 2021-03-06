from flask import Flask
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
executor = Executor(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activities.db'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
db = SQLAlchemy(app)

from stravastats import routes, utils

app.add_template_filter(utils.format_pace)
