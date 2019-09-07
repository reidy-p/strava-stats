from flask import Flask
from flask_executor import Executor

app = Flask(__name__)
executor = Executor(app)

from stravastats import routes
