from engine import processor
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

# App Configuration
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 # 10 MB
app.config["UPLOAD_EXTENSIONS"] = [".pdf"]

# Global Definitions
_globalDefs = {
    "appname": "RoboSpreader"
}

#
# Page Routes
#

# Home
@app.route("/")
def pageHome():
    return render_template("home.html", pageData=_globalDefs)

# Choose Page
@app.route("/choose-page", methods=["POST"])
def choosePage():
    return render_template("choose-page.html", pageData=_globalDefs)

# Upload file
@app.route("/upload-file", methods=["POST"])
def uploadFile():
    # Get uploaded file
    uploadedFile = request.files["file"]
    print(uploadedFile)

    # Save file
    # TODO: Create unique filename
    if uploadedFile.filename != "":
        uploadedFile.save(uploadedFile.filename)

    # TODO: Store filename in session
    
    return redirect("/choose-page")

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

    # Convert image to data
    validation_data = processor.processImage(page_image_string)

    return { "validation_data": validation_data }