import os
from uuid import uuid4 as make_uuid
from flask import Flask, jsonify, render_template, json, request
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

def lecturer_to_dict(json_string):
    data = json.loads(json_string)
    new_uuid = str(make_uuid())
    lecturer = {"UUID":new_uuid}
    for item in data:
        if item in ["tags", "contact"]:
            lecturer[item] = json.dumps(data[item])
        if item in COLUMNS:
            lecturer[item] = data[item]
    return lecturer

def row_to_lecturer(row):
    return {COLUMNS[i] : (json.loads(row[i]) if COLUMNS[i] in ["tags", "contact"] else row[i]) for i in range(len(COLUMNS)) if (not row[i] is None)}

def get_lecturer_row(uuid):
    cursor = db.get_db().execute('select * from lecturers where uuid = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route("/lecturer")
def lecturer_profile():
    with open("app/lecturer.json", encoding="UTF8") as file:
        lecturer = json.load(file)
    return render_template('lecturer.html', lecturer = lecturer)

@app.route("/lecturer/<uuid>")
def profile(uuid):
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    return render_template('lecturer.html', lecturer = row_to_lecturer(row))

COLUMNS = ["UUID", "title_before", "first_name", "middle_name", "last_name", "title_after",
           "picture_url", "location", "claim", "bio", "tags", "price_per_hour", "contact"]

@app.route("/api")
def api_request():
    return jsonify(secret="The cake is a lie")

@app.get("/api/lecturers")
def api_get_all_lecturers():
    cursor = db.get_db().execute('select * from lecturers')
    rows = cursor.fetchall()
    cursor.close()
    return jsonify([row_to_lecturer(row) for row in rows])

@app.post("/api/lecturers")
def api_add_lecturer():
    #data = json.loads(request.data)
    lecturer = lecturer_to_dict(request.data)
    new_uuid = str(make_uuid())
    lecturer["UUID"] = new_uuid
    values = ', '.join(['?' for _ in range(len(lecturer))])
    db.get_db().execute(
        'INSERT INTO lecturers (' + (', '.join([k for k in lecturer])) + ') VALUES ('+values+');',
        [lecturer[k] for k in lecturer])
    db.get_db().commit()
    row = get_lecturer_row(new_uuid)
    return row_to_lecturer(row)

@app.route("/api/lecturers/<uuid>", methods = ["GET", "PUT", "DELETE"])
def api_lecturer(uuid):
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    if request.method == "DELETE":
        db.get_db().execute("DELETE FROM lecturers WHERE uuid = ?", [uuid])
        db.get_db().commit()
        return 204
    if request.method == "GET":
        return jsonify(row_to_lecturer(row))
    if request.method == "PUT":
        lecturer = lecturer_to_dict(request.data)
        db.get_db().execute(
            'UPDATE lecturers SET '+ ', '.join([k+" = ?" for k in lecturer]) +' WHERE uuid = ?',
            [lecturer[k] for k in lecturer]+[uuid])
        db.get_db().commit()
        return jsonify(row_to_lecturer(row))

if __name__ == '__main__':
    app.run(debug=True)
