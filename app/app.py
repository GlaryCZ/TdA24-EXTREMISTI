import os

from flask import Flask, jsonify, render_template, json
from . import db

app = Flask(__name__)

app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, 'tourdeflask.sqlite'),
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

db.init_app(app)


@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route("/lecturer")
def lecturer_profile():
    with open("app/lecturer.json", encoding="UTF8") as file:
        lecturer = json.load(file)
    return render_template('lecturer.html', lecturer = lecturer)

@app.route("/api")
def api_request():
    return jsonify(secret="The cake is a lie")

if __name__ == '__main__':
    app.run(debug=True)
