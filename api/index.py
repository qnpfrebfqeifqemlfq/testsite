import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clock")
def clock():
    return render_template("clock.html", target="2026-05-25T16:36:50")

if __name__ == "__main__":
    app.run(debug=True)
