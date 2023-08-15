import sqlite3

from db import db
from engine import processor
from engine import test
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

    # Get test data
    test1_data, test2_data = test.get_test_data()
    
    return render_template("test.html", pageData=_globalDefs, test1_data=test1_data, test2_data=test2_data)

##### DEBUG ####

# Initialize 
@app.route("/initialize", methods=["GET"])
def initialize():
    db.initialize()
    table_data = [db.get_table("fields"), db.get_table("tests")]
    return render_template("status.html", pageData=_globalDefs, tables=table_data)

# Results
@app.route("/results", methods=["GET"])
def show_results():
    table_data = [db.get_table("results")]
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

# Create audio string
@app.route("/create-audio-string", methods=["POST"])
def createAudioString():

    # Get value string
    value_string = request.form.get("value-string", "")

    # Create audio string
    audio_string = processor.create_audio_string(value_string)

    return audio_string

#
# API Methods for Test
#

# Record test results
@app.route("/record-test-results", methods=["POST"])
def recordTestResults():

    # Get test result data
    test_id = int(request.form.get("test-id", -1))
    test_number = int(request.form.get("test-number"))
    start_time = request.form.get("test-start-time")
    end_time = request.form.get("test-end-time")
    input_values = request.form.get("test-values").split(",")

    # Calculate elapsed time
    elapsed_time_ms = int(end_time) - int(start_time)

    # Save test results to db
    test_id = test.save_test_results(test_id, test_number, elapsed_time_ms, input_values)

    return { "test_id": str(test_id) }