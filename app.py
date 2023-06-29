from flask import Flask, request, render_template

app = Flask(__name__)

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
@app.route("/choose-page")
def choosePage():
    return render_template("choose-page.html", pageData=_globalDefs)

# Upload file
@app.route("/upload-file", methods=["POST"])
def uploadFile():
    # Get uploaded file
    uploadedFile = request.files["file"]

    # Save file
    # TODO: Create unique filename
    if uploadedFile.filename != "":
        uploadedFile.save(uploadedFile.filename)

    # TODO: Store filename in session
    
    return redirect("/choose-page")

# Evaluate all languages
@app.route("/evaluate")
def pageEvaluateAll():
    _globalDefs["language"] = "all languages"
    return render_template("evaluate.html", pageData=_globalDefs)

#
# API Methods
#
