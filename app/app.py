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

def lecturer_row_dict(json_string):
    data = json.loads(json_string)
    lecturer = {}
    if "tags" in data:
        tag_list = []
        for tag in data["tags"]:
            if "uuid" in tag:
                tag_list.append(tag["uuid"])
            elif "name" in tag:
                row = get_tag("name", tag["name"])
                if row is None:
                    tag_uuid = str(make_uuid())
                    db.get_db().execute(
                        'INSERT INTO tags VALUES (?, ?);',
                        [tag_uuid, tag["name"]])
                    db.get_db().commit()
                else:
                    tag_uuid = row[0]
                tag_list.append(tag_uuid)
        lecturer["tags"]=json.dumps(tag_list)
        data.pop("tags")
    for item in data:
        if item in ["tags", "contact"]:
            lecturer[item] = json.dumps(data[item])
        if item in COLUMNS:
            lecturer[item] = data[item]
    return lecturer

def row_to_lecturer(row):
    data = {COLUMNS[i] : row[i] for i in range(len(COLUMNS)) if (not row[i] is None)}
    if "contact" in data:
        data["contact"] = json.loads(data["contact"])
    if "tags" in data:
        data["tags"] = [{"uuid":id, "name":get_tag("uuid", id)[1]} for id in json.loads(data["tags"])]
    return data

def get_lecturer_row(uuid):
    cursor = db.get_db().execute('select * from lecturers where uuid = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

def get_tag(param, value):
    cursor = db.get_db().execute('select * from tags where '+param+' = ?', [value])
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

COLUMNS = ["uuid", "title_before", "first_name", "middle_name", "last_name", "title_after",
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
    lecturer = lecturer_row_dict(request.data)
    new_uuid = str(make_uuid())
    lecturer["uuid"] = new_uuid
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
        return jsonify(204)
    if request.method == "GET":
        return jsonify(row_to_lecturer(row))
    if request.method == "PUT":
        lecturer = lecturer_row_dict(request.data)
        db.get_db().execute(
            'UPDATE lecturers SET '+ ', '.join([k+" = ?" for k in lecturer]) +' WHERE uuid = ?',
            [lecturer[k] for k in lecturer]+[uuid])
        db.get_db().commit()
        return jsonify(row_to_lecturer(row))

if __name__ == '__main__':
    app.run(debug=True)
