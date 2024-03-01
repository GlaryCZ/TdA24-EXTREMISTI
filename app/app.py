import os
from typing import List, Dict, Tuple, Callable
from uuid import uuid4 as make_uuid
from hashlib import sha256
from flask import Flask, jsonify, render_template, json, request, session, redirect, url_for
from . import db
from . import auto_maily

# to .env TODO: novej tag schvali admin, max pocet tagu Bootstrap

app = Flask(__name__)

app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, 'tourdeflask.sqlite'),
)

app.secret_key = 'asdsfydvgybhdcjsdniauayvfygcdsbahxsuyvigcdbh'

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

with app.app_context():
    db.init_db()
db.init_app(app)

def hash_password(password: str) -> str:
    """Returns a hashed password"""
    hashed_password = sha256(password.encode()).hexdigest()
    return hashed_password

def validate_login_info(uuid: str, password: str) -> Tuple[str, int]:
    """Checks if uuid and password is correct.
    
    Returns tuple(json error message, error code)

    When login info is correct then error code = 200
    """
    cursor = db.get_db().execute('SELECT hashed_password FROM lecturers_login WHERE UUID = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        return "User not found", 404
    if row[0] != hash_password(password):
        return "Wrong password", 401
    return "Login info correct", 200

def require_login(func: Callable) -> Callable:
    """Decorator for checking login info before showing a page.

    Returns an error page if there is no one logged in or the password is incorrect.
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
        return jsonify(code=res[1], message=res[0]), res[1]
    new_f.__name__ = func.__name__
    return new_f

def lecturer_row_dict(json_string: str) -> Dict:
    """Formats a lecturer json string into a lecturer dictionary."""
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
        if data[item] is None: continue
        if item in ["tags", "contact"]:
            lecturer[item] = json.dumps(data[item])
        elif item in COLUMNS:
            lecturer[item] = data[item]
    return lecturer

def row_to_lecturer(row: List) -> Dict:
    """Formats a database row into lecturer dictionary."""
    data = {COLUMNS[i] : row[i] for i in range(len(COLUMNS))}
    if "price_per_hour" in data and not data["price_per_hour"] is None:
        try:
            data["price_per_hour"] = int(data["price_per_hour"])
        except:
            data["price_per_hour"] = None
    if "contact" in data and not data["contact"] is None:
        data["contact"] = json.loads(data["contact"])
    if "tags" in data and not data["tags"] is None:
        try:
            data["tags"] = [{"uuid":id, "name":get_tag("uuid", id)[1]} for id in json.loads(data["tags"])]
        except:
            data["tags"] = []
    return data

def get_lecturer_row(uuid: str) -> List:
    """Get a lecturer row from SQL databse.

    You may need to convert this row using row_to_lecturer(row).
    """
    cursor = db.get_db().execute('select * from lecturers where uuid = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

def get_tag(param, value) -> List:
    """Get a tag from SQL databse.
    
    :param: can be only "name" or "uuid".
    """
    cursor = db.get_db().execute('select * from tags where '+ param +' = ?', [value])
    row = cursor.fetchone()
    cursor.close()
    return row

def get_all_tags() -> List:
    """Get all tags from SQL databse."""
    cursor = db.get_db().execute('select * from tags')
    rows = cursor.fetchall()
    cursor.close()
    return [{"uuid":row[0], "name":row[1]}for row in rows]

def get_locations() -> List:
    cursor = db.get_db().execute('SELECT location FROM lecturers')
    loc = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return loc

def get_time() -> List:
    cursor = db.get_db().execute('SELECT date_and_time FROM aproved_orders')
    time = [row[0] for row in cursor.fetchall()][0]
    cursor.close()
    return time

def get_lec_name(uuid : str) -> List:
    cursor = db.get_db().execute('SELECT first_name FROM lecturers WHERE uuid = ?', [uuid])
    lec_name = [row[0] for row in cursor.fetchall()][0]
    cursor = db.get_db().execute('SELECT last_name FROM lecturers WHERE uuid = ?', [uuid])
    lec_lname = [row[0] for row in cursor.fetchall()][0]
    cursor.close()
    return (lec_name + " " + lec_lname)



@require_login
def get_orders_for_lecturer(table):
    '''Returns list of lists with info of each order of currently logged in user'''
    cursor = db.get_db().execute(
        f'SELECT * FROM {table} WHERE uuid = ?',
        [session['uuid']]
    )
    rows = cursor.fetchall()
    cursor.close()
    all_orders = [[r for r in row] for row in rows]
    return all_orders

@app.route('/login', methods = ["GET", 'POST'])
def lecturer_login():
    if request.method == "GET":
        return render_template("login-lecturer.html")
    data = dict(request.form)
    cursor = db.get_db().execute('SELECT uuid FROM lecturers_login WHERE username = ?', [data['username']])
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        return jsonify(code=404, message="Username not found"), 404 #TODO make this a popup
    uuid = row[0]
    session["uuid"] = None
    session["password"] = None
    session["my_lecturer"] = None
    res = validate_login_info(uuid, data['password'])
    if res[1] != 200:
        return jsonify(code=res[1], message=res[0]), res[1] #TODO make this a popup
    session["uuid"] = uuid
    session["password"] = data['password']
    session["my_lecturer"] = row_to_lecturer(get_lecturer_row(uuid))
    return redirect(url_for("lecturer_private_profile"))

@app.route('/logout-lecturer', methods = ["GET"])
def lecturer_logout():
    session["uuid"] = None
    session["password"] = None
    session["my_lecturer"] = None
    return redirect(url_for("lecotrs_search_page"))

@app.route('/register-lecturer', methods = ["GET", 'POST'])
def lecturer_registration():
    if request.method == "GET":
        return render_template("register-lecturer.html")
    cursor = db.get_db().execute('SELECT username FROM lecturers_login')
    rows = cursor.fetchall()
    cursor.close()
    claimed_names = [i[0] for i in rows]
    data = dict(request.form)
    if any(data[i] == "" for i in data):
        return jsonify(code=404, message="Missing required field"), 404 #TODO make this a popup
    if data['username'] in claimed_names:
        return jsonify(code=404, message="Username already used"), 404 #TODO make this a popup
    new_uuid = str(make_uuid())
    db.get_db().execute(
        'INSERT INTO lecturers (uuid, first_name, last_name, contact) VALUES (?,?,?,?);',
        [new_uuid, data["first_name"], data["last_name"], '{"telephone_numbers":["'+data["telephone_number"]+'"],"emails":["'+data["email"]+'"]}'])
    db.get_db().execute(
        'INSERT INTO lecturers_login (UUID, hashed_password, username) VALUES (?,?,?);',
        [new_uuid, hash_password(data["password"]), data["username"]])
    db.get_db().commit()
    session["uuid"] = new_uuid
    session["password"] = data['password']
    session["my_lecturer"] = row_to_lecturer(get_lecturer_row(new_uuid))
    return redirect(url_for("lecturer_private_profile"))

@app.route('/', methods = ["GET", "POST"])
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
    location = get_locations()    
    cursor = db.get_db().execute("SELECT MAX(price_per_hour) FROM lecturers; ")
    max_price = cursor.fetchone()[0]
    cursor.close()
    return render_template('lectors-search-page.html', lecturers = lecturers, tags = get_all_tags(), last_searched = data, max_price = max_price, locations = location)

@app.route("/my_profile/edit", methods=['GET', 'POST'])
@require_login
def lecturer_edit_profile():
    if request.method == "POST":
        data = dict(request.form)
        lecturer = {key:value for key, value in data.items() if (key in COLUMNS) and (value != "") and (not value is None)}
        emails = [value for key, value in data.items() if ("email" in key) and (value != "") and (not value is None)]
        telephone_numbers = [value for key, value in data.items() if ("tel" in key) and (value != "") and (not value is None)]
        lecturer["contact"] = json.dumps({"telephone_numbers":telephone_numbers, "emails":emails})
        tags = [key[3:] for key, value in data.items() if key[:3]=="tag" and value=="on"]
        lecturer["tags"] = json.dumps(tags)
        print(data)
        print(lecturer)
        db.get_db().execute(
            'UPDATE lecturers SET '+ ', '.join([k+" = ?" for k in lecturer]) +' WHERE uuid = ?',
            [lecturer[k] for k in lecturer]+[session["uuid"]])
        db.get_db().commit()
        session["my_lecturer"] = row_to_lecturer(get_lecturer_row(session["uuid"]))
    return render_template("lecturer-edit.html", tags=get_all_tags(), mytags=[i["uuid"] for i in session["my_lecturer"]["tags"]])

@app.route("/my_profile", methods=['GET', 'POST'])
@require_login
def lecturer_private_profile():
    if request.method == 'POST':
        data = dict(request.form) # TODO
        try:
            auto_maily.mail(data['submit'], data['email'], data['message'], get_lec_name(data['uuid']), get_time())
            
        except ValueError:
                ("Wrong email!")
        print(data)
        if data['submit'] == 'ano':
            db.get_db().execute(
                'INSERT INTO aproved_orders (uuid, first_name, last_name, email, phone_number, tags, meet_type, date_and_time, message_for_lecturer) VALUES (?,?,?,?,?,?,?,?,?);',
                [data['uuid'], data["first_name"], data["last_name"], data['email'], data['phone_number'], str(data['tags']), data['meet_type'], data['date_and_time'], data['message']]
            )
        db.get_db().execute("DELETE FROM orders WHERE date_and_time = ? and uuid = ? and tags=?", 
                            [data['date_and_time'], data['uuid'], str(data['tags'])])
        db.get_db().commit()
        cursor = db.get_db().execute('SELECT * FROM aproved_orders')
        rows = cursor.fetchall()
        cursor.close()
        print(rows)

    orders_info = get_orders_for_lecturer('orders')
    for order in orders_info:
        order[5] = order[5].strip("][").replace("'", '').split(', ')
    return render_template('lecturer-logged-in.html', orders=orders_info)

@app.route("/my_profile/approved-orders", methods=['GET', 'POST'])
@require_login
def approved_orders():
    if request.method == 'POST':
        # TODO:
        return 'POST'
    orders_info = get_orders_for_lecturer('aproved_orders')
    for order in orders_info:
        order[5] = order[5].strip("][").replace("'", '').split(', ')
    return render_template('approved-orders.html', orders=orders_info)

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
    print(data)
    if not "password" in data or data["password"] is None:
        return jsonify(code=404, message="Missing password"), 404
    if not "username" in data or data["username"] is None:
        return jsonify(code=404, message="Missing username"), 404
    if not "first_name" in data or data["first_name"] is None:
        return jsonify(code=404, message="Missing required parameters first_name"), 404
    if not "last_name" in data or data["last_name"] is None:
        return jsonify(code=404, message="Missing required parameters last_name"), 404
    if ("contact" in data and (not data["contact"] is None) and
        any((not p in data["contact"] or data["contact"][p] is None) for p in ["telephone_numbers", "emails"])):
        return jsonify(code=404, message="Missing required parameters in contacts"), 404
    lecturer = lecturer_row_dict(request.data)
    new_uuid = str(make_uuid())
    lecturer["uuid"] = new_uuid
    values = ', '.join(['?' for _ in lecturer])
    db.get_db().execute(
        'INSERT INTO lecturers (' + (', '.join([k for k in lecturer])) + ') VALUES ('+values+');',
        [lecturer[k] for k in lecturer])
    db.get_db().execute(
        'INSERT INTO lecturers_login (UUID, hashed_password, username) VALUES (?,?,?);',
        [new_uuid, hash_password(data["password"]), data["username"]])
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
        return jsonify(code=res[1], message=res[0]), res[1]
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
    if request.method == "GET":
        row = get_lecturer_row(uuid)
        if row is None:
            return jsonify(code=404, message="User not found"), 404
        lecturer = row_to_lecturer(row)
        # print(lecturer.tag)
        return render_template('order-lecturer.html', lecturer = lecturer)
    else:
        data = dict(request.form)
        my_tags_uuids = [t for t in data if not t in ['first-name', 'last-name', 'email', 'phone-number', 'meet-type', 'date', 'message']]
        my_tags = [get_tag("uuid", id)[1] for id in my_tags_uuids]
        # return f'{data}'
        new_dict = {key: val for key, val in data.items() if key != 'message'}
        if any(new_dict[i] == "" for i in new_dict):
            return jsonify(code=404, message="Missing required field"), 404 #TODO make this a popup
        db.get_db().execute(
            'INSERT INTO orders (uuid, first_name, last_name, email, phone_number, tags, meet_type, date_and_time, message_for_lecturer, order_id) VALUES (?,?,?,?,?,?,?,?,?,?);',
            [uuid, data["first-name"], data["last-name"], data['email'], data['phone-number'], str(my_tags), data['meet-type'], data['date'], data['message'], make_uuid().int>>32] # TODO:
        )
        db.get_db().commit()


        row = get_lecturer_row(uuid)
        return render_template('order-confirmation.html', lecturer = row_to_lecturer(row), email=data['email'])
    

    
@app.route("/login/monthly-calendar", methods = ["GET"])
def calendar_monthly():
    return render_template('calendar-monthly.html')


if __name__ == '__main__':
    app.run(debug=True)
