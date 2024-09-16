from flask import Flask
import os

app = Flask(__name__)

# Set 'ENV' in app.config using os.getenv to fetch environment variable or set a default
app.config['ENV'] = os.getenv('ENV', 'development')

# Now check the value of ENV safely
if app.config['ENV'] == 'production':
    app.config.from_object("config.ProductionConfig")
elif app.config['ENV'] == 'testing':
    app.config.from_object("config.TestingConfig")
else:
    app.config.from_object("config.DevelopmentConfig")

from app import views

