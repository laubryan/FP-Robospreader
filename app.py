from engine import processor
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

# App Configuration
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 # 10 MB
app.config["UPLOAD_EXTENSIONS"] = [".pdf"]

# Global Definitions
_globalDefs = {
    "appname": "RoboSpreader",
}

#
# Page Routes
#

# Home
@app.route("/")
def pageHome():
    return render_template("home.html", pageData=_globalDefs)

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
    try:
        validation_data = processor.process_image(page_image)
    except:
        validation_data = []

    return { "validation_data": validation_data }

# Create audio string
@app.route("/create-audio-string", methods=["POST"])
def createAudioString():

    # Get value string
    value_string = request.form.get("value-string", "")

    # Create audio string
    audio_string = processor.create_audio_string(value_string)

    return { "audio_string": audio_string }
