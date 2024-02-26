import os
from typing import List, Dict, Tuple, Callable
from uuid import uuid4 as make_uuid
from hashlib import sha256
from flask import Flask, jsonify, render_template, json, request, session, redirect, url_for
# from authlib.integrations.flask_client import OAuth
from . import db
from . import auto_maily

CLIENT_ID = '661793370921-cih2ksvgggmhbrvobt0l6lua4l483orp.apps.googleusercontent.com'
CLIENT_SECRET = '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'

SCOPE = 'https://www.googleapis.com/auth/calendar'

app = Flask(__name__)

app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, 'tourdeflask.sqlite'),
)

def save_request_token(token):
    print('ref_token: '+token)

def fetch_request_token():
    print('ziskej rer_token')
'''
app.secret_key = "56675hdd6shd74setj7474jst7878s1jt"
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='661793370921-cih2ksvgggmhbrvobt0l6lua4l483orp.apps.googleusercontent.com',
    client_secret='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',
    client_kwargs={'scope': 'openid https://www.googleapis.com/auth/calendar'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    # authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    offline=True,
    prompt='consent',
    approval_prompt='force',
    access_type='offline',
    refresh_token_url=None,
    save_request_token=save_request_token,
    fetch_request_token=fetch_request_token,
    GOOGLE_REFRESH_TOKEN_URL=None
)
'''

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
    """Formats a lecturer json string into a row for saving in the SQL database."""
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
        data["price_per_hour"] = int(data["price_per_hour"])
    if "contact" in data and not data["contact"] is None:
        data["contact"] = json.loads(data["contact"])
    if "tags" in data and not data["tags"] is None:
        data["tags"] = [{"uuid":id, "name":get_tag("uuid", id)[1]} for id in json.loads(data["tags"])]
    return data

def get_lecturer_row(uuid: str) -> List:
    """Get a lecturer row from SQL databse.

    You may need to convert this row using row_to_lecturer(row).
    """
    cursor = db.get_db().execute('select * from lecturers where uuid = ?', [uuid])
    row = cursor.fetchone()
    cursor.close()
    return row

def get_tag(param: str, value) -> List:
    """Get a tag from SQL databse.
    
    :param: can be only "name" or "uuid".
    """
    cursor = db.get_db().execute('select * from tags where '+param+' = ?', [value])
    row = cursor.fetchone()
    cursor.close()
    return row

@require_login
def get_orders_for_lecturer():
    '''Returns list of lists with info of each order of currently logged in user'''
    cursor = db.get_db().execute(
        'SELECT * FROM orders WHERE uuid = ?',
        [session['uuid']]
    )
    rows = cursor.fetchall()
    cursor.close()
    all_orders = [[r for r in row] for row in rows]
    return all_orders
'''
@app.route('/', methods = ["GET"])
def homepage():
    # TODO
    return render_template("homepage.html")
'''
'''
@app.route('/my_profile/caledar_auth')
def calendar_login():
    # return redirect('https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=https%3A%2F%2F127.0.0.1:5000&prompt=consent&response_type=code&client_id={}&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&access_type=offline'.format('661793370921-cih2ksvgggmhbrvobt0l6lua4l483orp.apps.googleusercontent.com'))
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/my_profile/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token(access_type='offline')  # Access token from google (needed to get user info)
    print(token)
    # print(token['refresh_token'])
    resp = google.get('userinfo', token=token)  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session['access_token'] = token['access_token']
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    return redirect('/my_profile')
'''

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

    cursor = db.get_db().execute('SELECT * FROM tags')
    rows = cursor.fetchall()
    cursor.close()
    tags = [{"uuid":row[0], "name":row[1]}for row in rows]
    
    cursor = db.get_db().execute("SELECT MAX(price_per_hour) FROM lecturers; ")
    max_price = cursor.fetchone()[0]
    cursor.close()
    return render_template('lectors-search-page.html', lecturers = lecturers, tags = tags, last_searched = data, max_price = max_price)

@app.route("/my_profile", methods=['GET', 'POST'])
@require_login
def lecturer_private_profile():
    if request.method == 'POST':
        
        data = dict(request.form) # TODO
        auto_maily.mail(data['submit'], data['email'], data['message'])
        return data
    orders_info = get_orders_for_lecturer()
    for order in orders_info:
        order[5] = order[5].strip("][").replace("'", '').split(', ')
    return render_template('lecturer-logged-in.html', orders=orders_info)

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
            'INSERT INTO orders (uuid, first_name, last_name, email, phone_number, tags, meet_type, date_and_time, message_for_lecturer) VALUES (?,?,?,?,?,?,?,?,?);',
            [uuid, data["first-name"], data["last-name"], data['email'], data['phone-number'], str(my_tags), data['meet-type'], data['date'], data['message']]
        )
        db.get_db().commit()


        row = get_lecturer_row(uuid)
        return render_template('order-confirmation.html', lecturer = row_to_lecturer(row), email=data['email'])
    

    
@app.route("/login/monthly-calendar", methods = ["GET"])
def calendar_monthly():
    return render_template('calendar-monthly.html')

if __name__ == '__main__':
    app.run(debug=True)
