from flask import Flask
from flask_cors import CORS
from datetime import timedelta
from flask_jwt_extended import JWTManager

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

app.config["JWT_SECRET_KEY"] = "xls**/54199021Nanaas4d8asdxs4/7/6238742347--.@"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(app)

from app.request import *
