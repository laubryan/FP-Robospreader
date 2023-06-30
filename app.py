from flask import Flask, request, render_template, redirect
from engine import processor

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
# API Methods
#

# Process page image
@app.route("/process-page-image", methods=["POST"])
def processPageImage():

    # Get image buffer from client
    page_image = request.form.get("image-buffer", None)
    print(f"Received buffer: {len(page_image)} bytes")

    # DEBUG
    validationData = [
        { "label": "Short-term investments", "extracted_value": "3799", "original_value": "3799" },
        { "label": "Accounts receivable", "extracted_value": "926", "original_value": "926" },
        { "label": "Total current assets", "extracted_value": "7516", "original_value": "7516" },
        { "label": "Investments deposits and other assets", "extracted_value": "936", "original_value": "936" },
        { "label": "Deferred income tax", "extracted_value": "134", "original_value": "134" },
        { "label": "Total current liabilities", "extracted_value": "7775", "original_value": "7775" },
        { "label": "Total shareholders equity", "extracted_value": "4400", "original_value": "4400" },
    ]

    return { "validation_data": validationData }