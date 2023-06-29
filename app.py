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

# Evaluate all languages
@app.route("/evaluate")
def pageEvaluateAll():
    _globalDefs["language"] = "all languages"
    return render_template("evaluate.html", pageData=_globalDefs)

#
# API Methods
#
