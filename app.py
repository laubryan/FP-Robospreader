import sqlite3

from db import db
from engine import processor
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

# App Configuration
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 # 10 MB
app.config["UPLOAD_EXTENSIONS"] = [".pdf"]

# Global Definitions
_globalDefs = {
    "appname": "RoboSpreader",
    "db": sqlite3.connect("db/test.db")
}

#
# Page Routes
#

# Home
@app.route("/")
def pageHome():
    return render_template("home.html", pageData=_globalDefs)

# Test
@app.route("/test", methods=["GET"])
def pageTest():
    return render_template("test.html", pageData=_globalDefs)

# Initialize (DEV ONLY)
@app.route("/initialize", methods=["GET"])
def initialize():
    db.initialize()
    table_data = [db.get_table("fields"), db.get_table("tests")]
    return render_template("status.html", pageData=_globalDefs, tables=table_data)

#
# Errors
#
def app_error(e):
    return render_template("error.html", pageData=_globalDefs)

# Register error handlers
app.register_error_handler(404, app_error)
app.register_error_handler(500, app_error)

#
# API Methods
#

# Process page image
@app.route("/process-page-image", methods=["POST"])
def processPageImage():

    # Get image buffer string from client
    page_image_string = request.form.get("image-buffer", None)

    # Convert image string to image
    page_image = processor.convert_image_string(page_image_string)

    # Convert image to data
    validation_data = processor.process_image(page_image)

    return { "validation_data": validation_data }