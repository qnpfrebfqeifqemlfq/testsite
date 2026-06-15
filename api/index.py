import os
from flask import Flask, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, '../templates'))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '../static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clock")
def clock():
    return render_template("clock.html", target="2026-05-25T16:36:50")

if __name__ == "__main__":
    app.run(debug=True)
