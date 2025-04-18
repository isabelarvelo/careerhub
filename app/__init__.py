from flask import Flask

# __name__ is the package name - 'app', for locating templates and static files
app = Flask(__name__)

from app import career_hub # needs to match script to enable database and service, bridge between db and web service, eg. career-hub

