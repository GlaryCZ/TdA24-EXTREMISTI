import os
from uuid import uuid4 as make_uuid
from hashlib import sha256
from flask import Flask, jsonify, render_template, json, request, session, redirect, url_for
from . import db

app = Flask(__name__)

app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, 'tourdeflask.sqlite'),
)

app.secret_key = "56675hdd6shd74setj7474jst7878s1jt"

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# with app.app_context():
#     db.init_db()
db.init_app(app)

def get_login_info(uuid):
    """Get hashed password from SQL databse."""
    cursor = db.get_db().execute('SELECT hashed_password FROM lecturers_login WHERE UUID = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

def hash_password(password):
    """Returns a hashed password"""
    hashed_password = sha256(password.encode()).hexdigest()
    return hashed_password

def validate_login_info(uuid, password):
    """Checks if uuid and password is correct.
    
    Returns tuple(json error message, error code)

    When login info is correct then error code = 200
    """
    row = get_login_info(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    if row[0] != hash_password(password):
        return jsonify(code=401, message="Wrong password"), 401
    return jsonify(code=200, message="Login info correct"), 200

def require_login(func):
    """Decorator for checking login info before showing a page.

    Returns an error page if there is noone logged in or the password is incorrect.
    Otherewise shows the page normally.

    Example:

    @app.route("/private_page")\n
    @require_login\n
    def private_page:
        ...
    """
    def new_f(*args, **kwargs):
        if (not ('uuid' in session)) or session['uuid'] is None:
            return jsonify(code=404, message="Not loggged in"), 404
        res = validate_login_info(session['uuid'], session['password'])
        if res[1] == 200:
            return func(*args, **kwargs)
        return res
    new_f.__name__ = func.__name__
    return new_f

def lecturer_row_dict(json_string):
    """Formats a lecturer json string into a row for saving in the SQL database."""
    data = json.loads(json_string)
    print(data)
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
        if data[item] is None: continue
        if item in ["tags", "contact"]:
            lecturer[item] = json.dumps(data[item])
        elif item in COLUMNS:
            lecturer[item] = data[item]
    return lecturer

def row_to_lecturer(row):
    """Formats a database row into lecturer json."""
    data = {COLUMNS[i] : row[i] for i in range(len(COLUMNS))}
    if "price_per_hour" in data and not data["price_per_hour"] is None:
        data["price_per_hour"] = int(data["price_per_hour"])
    if "contact" in data and not data["contact"] is None:
        data["contact"] = json.loads(data["contact"])
    if "tags" in data and not data["tags"] is None:
        data["tags"] = [{"uuid":id, "name":get_tag("uuid", id)[1]} for id in json.loads(data["tags"])]
    return data

def get_lecturer_row(uuid):
    """Get a lecturer row from SQL databse.

    You may need to convert this row using row_to_lecturer(row).
    """
    cursor = db.get_db().execute('select * from lecturers where uuid = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

def get_tag(param, value):
    """Get a tag from SQL databse.
    
    :param: can be only "name" or "uuid".
    """
    cursor = db.get_db().execute('select * from tags where '+param+' = ?', [value])
    row = cursor.fetchone()
    cursor.close()
    return row

@app.route('/', methods = ["GET"])
def homepage():
    # TODO
    return render_template("homepage.html")

@app.route('/login-lecturer', methods = ["GET", 'POST'])
def lecturer_login():
    if request.method == "GET":
        return render_template("login-lecturer.html")
    data = dict(request.form)
    session["uuid"] = None
    session["password"] = None
    session["my_lecturer"] = None
    res = validate_login_info(data['uuid'], data['password'])
    if res[1] != 200:
        return res #TODO make this a popup
    session["uuid"] = data['uuid']
    session["password"] = data['password']
    session["my_lecturer"] = row_to_lecturer(get_lecturer_row(data['uuid']))
    return redirect(url_for("lecturer_private_profile"))

 #TODO logout page

 #TODO registration page

@app.route('/search', methods = ["GET", "POST"])
def lecotrs_search_page():
    parameters = {}
    my_tags = []
    data = {}
    if request.method == "POST":
        data = dict(request.form)
        if "min_price" in data and data["min_price"] !='':
            parameters["price_per_hour >= ?"] = data["min_price"]
        if "max_price" in data and data["max_price"] !='':
            parameters["price_per_hour <= ?"] = data["max_price"]
        if "location" in data and data["location"] !='':
            parameters["location = ?"] = data["location"]
        my_tags = [t for t in data if not t in ["min_price","max_price","location"]]
    
    cursor = db.get_db().execute(
        'SELECT * FROM lecturers' + (' WHERE 'if len(parameters) > 0 else'') +
        ' AND '.join([k for k in parameters]), [parameters[k] for k in parameters])
    rows = cursor.fetchall()
    cursor.close()
    lecturers = [row_to_lecturer(row) for row in rows]
    lecturers = [k for k in lecturers if all(tag in [i["uuid"] for i in k["tags"]] for tag in my_tags)]

    cursor = db.get_db().execute('SELECT * FROM tags')
    rows = cursor.fetchall()
    cursor.close()
    tags = [{"uuid":row[0], "name":row[1]}for row in rows]
    
    cursor = db.get_db().execute("SELECT MAX(price_per_hour) FROM lecturers; ")
    max_price = cursor.fetchone()[0]
    cursor.close()
    return render_template('lectors-search-page.html', lecturers = lecturers, tags = tags, last_searched = data, max_price = max_price)

@app.route("/my_profile")
@require_login
def lecturer_private_profile():
    return render_template('lecturer-logged-in.html')

@app.route("/lecturer/<uuid>")
def profile(uuid):
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    return render_template('lecturer.html', lecturer = row_to_lecturer(row))

COLUMNS = ["uuid", "title_before", "first_name", "middle_name", "last_name", "title_after",
           "picture_url", "location", "claim", "bio", "tags", "price_per_hour", "contact"]

@app.get("/api/lecturers")
def api_get_all_lecturers():
    cursor = db.get_db().execute('select * from lecturers')
    rows = cursor.fetchall()
    cursor.close()
    return jsonify([row_to_lecturer(row) for row in rows])

@app.post("/api/lecturers")
def api_add_lecturer():
    data = json.loads(request.data)
    if not "password" in data or data["password"] is None:
        return jsonify(code=404, message="Missing password"), 404
    if not "first_name" in data or data["first_name"] is None:
        return jsonify(code=404, message="Missing required parameters first_name"), 404
    if not "last_name" in data or data["last_name"] is None:
        return jsonify(code=404, message="Missing required parameters last_name"), 404
    if ("contact" in data and (not data["contact"] is None) and
        any((not p in data["contact"] or data["contact"][p] is None) for p in ["telephone_numbers", "emails"])):
        return jsonify(code=404, message="Missing required parameters in contacts"), 404
    lecturer = lecturer_row_dict(request.data)
    print(lecturer)
    new_uuid = str(make_uuid())
    lecturer["uuid"] = new_uuid
    values = ', '.join(['?' for _ in lecturer])
    db.get_db().execute(
        'INSERT INTO lecturers (' + (', '.join([k for k in lecturer])) + ') VALUES ('+values+');',
        [lecturer[k] for k in lecturer])
    db.get_db().execute(
        'INSERT INTO lecturers_login (UUID, hashed_password) VALUES (?,?);',
        [new_uuid, hash_password(data["password"])])
    db.get_db().commit()
    row = get_lecturer_row(new_uuid)
    return row_to_lecturer(row)

@app.get("/api/lecturers/<uuid>")
def api_lecturer_get(uuid):
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    return jsonify(row_to_lecturer(row))

@app.route("/api/lecturers/<uuid>&<password>", methods = ["PUT", "DELETE"])
def api_lecturer_edit(uuid, password):
    res = validate_login_info(uuid, password)
    if res[1] != 200:
        return res
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    if request.method == "DELETE":
        db.get_db().execute("DELETE FROM lecturers WHERE uuid = ?", [uuid])
        db.get_db().commit()
        return jsonify(code=204, message="Profile deleted"), 204
    elif request.method == "PUT":
        lecturer = lecturer_row_dict(request.data)
        db.get_db().execute(
            'UPDATE lecturers SET '+ ', '.join([k+" = ?" for k in lecturer]) +' WHERE uuid = ?',
            [lecturer[k] for k in lecturer]+[uuid])
        db.get_db().commit()
        row = get_lecturer_row(uuid)
        return jsonify(row_to_lecturer(row))
    
@app.route("/order/<uuid>", methods = ["GET", "POST"])
def order_page(uuid):
    row = get_lecturer_row(uuid)
    if row is None:
        return jsonify(code=404, message="User not found"), 404
    return render_template('order-lecturer.html', lecturer = row_to_lecturer(row))
    
@app.route("/login/monthly-calendar", methods = ["GET"])
def calendar_monthly():
    return render_template('calendar-monthly.html')

if __name__ == '__main__':
    app.run(debug=True)
