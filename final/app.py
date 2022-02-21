import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, flash
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy.sql.visitors import VisitableType
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
import secrets
import psycopg2
from werkzeug.utils import secure_filename

from helpers import login_required

# Thanks to https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/ for guide on how to allow user uploads
UPLOAD_FOLDER = "./static/imgs"
ALLOWED_EXTENSIONS = set(["jpg", "jpeg", "png"])
images = "static/imgs/"

# configure app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Thanks to https://www.youtube.com/watch?v=w25ea_I89iM Traversy Media for connecting to and querying the database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:dbase@localhost/petca"
# !!!!!TODO!!!!!! Configure CS50 Library to use SQLite database - !!!!!!!!TODO!!!!!!!!
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User table
class users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String)
    guest_pass = db.Column(db.String, unique=True)

    def __init__(self, email, password, guest_pass):
        self.email = email
        self.password = password
        self.guest_pass = guest_pass

# Pet important info table
class pets(db.Model):
    __tablename__ = "pets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.VARCHAR(30))
    birthdate = db.Column(db.Date, nullable=True)
    species = db.Column(db.VARCHAR(30))
    sex = db.Column(db.VARCHAR(10), nullable=True)
    traits = db.Column(db.VARCHAR(100), nullable=True)
    food = db.Column(db.VARCHAR(100))
    feed_freq = db.Column(db.String)
    vet = db.Column(db.VARCHAR(100))
    vet_num = db.Column(db.VARCHAR(20))
    env = db.Column(db.Text, nullable=True)
    picpath = db.Column(db.String)
    pic = db.Column(db.String, unique=True)
    notes = db.Column(db.Text, nullable=True)


    def __init__(self, user_id, name, birthdate, species, sex, traits, food, feed_freq, vet, vet_num, env, picpath, pic, notes):
        self.user_id = user_id
        self.name = name
        self.birthdate = birthdate
        self.species = species
        self.sex = sex
        self.traits = traits
        self.food = food
        self.feed_freq = feed_freq
        self.vet = vet
        self.vet_num = vet_num
        self.env = env
        self.picpath = picpath
        self.pic = pic
        self.notes = notes



class meds(db.Model):
    __tablename__ = "meds"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    pet_id = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer)
    medstat = db.Column(db.Boolean, default=False)
    medication = db.Column(db.VARCHAR(30))
    dosage = db.Column(db.VARCHAR(30))
    datestart = db.Column(db.Date, nullable=True)
    dateend = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text)
    dateentry = db.Column(db.Date)

    
    def __init__(self, user_id, pet_id, weight, medstat, medication, dosage, datestart, dateend, notes, dateentry):
        self.pet_id = pet_id
        self.user_id = user_id
        self.weight = weight
        self.medstat = medstat
        self.medication = medication
        self.dosage = dosage
        self.datestart = datestart
        self.dateend = dateend
        self.notes = notes
        self.dateentry = dateentry

#db.drop_all()
#db.create_all()

# FUUUNNNctions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def img_name(filename):
    ext = "." + filename.rsplit('.', 1)[1]
    x = secrets.token_urlsafe()
    if db.session.query(pets).filter(pets.pic == x).count() != 0:
        img_name()
    else:
        x = x + ext
        return x

def guestp():
    x = secrets.token_urlsafe()
    if db.session.query(users).filter(users.guest_pass == x).count() != 0:
        guestp()
    else:
        return x

# Intro page for all visitors
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect("/edit")
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect("/edit")
        # Check DB for entry        
        edit_id = request.form["edit"]    
        update = db.session.query(pets).filter(pets.id == edit_id).first()
        if file and update.pic != None and allowed_file(file.filename):
            filename = update.pic
            file.save(os.path.join(images + filename))
            return redirect("/edit")
            
        if file and allowed_file(file.filename):
            filename = img_name(file.filename)
            filename = secure_filename(filename)
               
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        
        pic = filename
        update.pic = pic
        db.session.commit()

        flash("Image uploaded")
        return redirect("/home")
    return redirect("/home")

# Thanks to CS50 for the login function (Pset Finance)
@app.route("/login", methods=["GET", "POST"])
def login():
        # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            error = "Enter valid username"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        if not request.form.get("password"):
            error = "Enter valid password"
            return render_template("login.html", error=error)

        # Query database for username
        #rows = db.session.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))
        rows = db.session.query(users).filter_by(email=request.form.get("email")).first()
        
        # Ensure username exists and password is correct
        if rows == None or not check_password_hash(rows.password, request.form.get("password")):
            error = "Invalid username and/or password"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows.id

        # Redirect user to home page
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        email = request.form.get("email")
        if db.session.query(users).filter(users.email == email).count() != 0:
            error = "Email already registered"
            return render_template("register.html", error=error)
        password = request.form.get("password")
        if len(password) < 8:
            error = "Password must be at least 8 characters"
            return render_template("register.html", error=error)
        confirm = request.form.get("confirm")
        if password != confirm:
            error = "Passwords do not match"
            return render_template("register.html", error=error)
        if db.session.query(users).filter(users.email == email).count() == 0:
            guest_pass = guestp()
            password = generate_password_hash(password)
            data = users(email, password, guest_pass)
            db.session.add(data)
            db.session.commit()
            return redirect("/login")

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "GET":
        info = db.session.query(users).filter(users.id == session["user_id"]).first()
        return render_template("account.html", info=info)
    else:
        newemail = request.form.get("email")
        password = request.form.get("password")
        if len(password) < 8:
            error = "Password must be at least 8 characters"
            return render_template("account.html", error=error)
        confirm = request.form.get("confirm")
        if password != confirm:
            error = "Passwords do not match"
            return render_template("account.html", error=error)
        password = generate_password_hash(password)
        update = db.session.query(users).filter(users.id == session["user_id"]).first()
        update.email = newemail
        update.password = password
        db.session.commit()
        return redirect("/home")


@app.route("/addpet", methods=["GET", "POST"])
@login_required
def addpet():
    if request.method == "GET":
        return render_template("addpet.html")
    else:
        name = request.form.get("name")
        birthdate = request.form.get("birthdate")
        if birthdate == "":
            birthdate = None
        species = request.form.get("species")
        sex = request.form.get("sex")
        traits = request.form.get("traits")
        food = request.form.get("food")
        feed_freq = request.form.get("feed_freq")
        if species == None or traits == None or food == None or feed_freq == None or name == None:
            error = "Please enter required fields"
            return render_template("addpet.html", error=error)
        vet = request.form.get("vet")
        vet_num = request.form.get("vet_num")
        env = request.form.get("env")
        picpath = images
        pic = None
        notes = request.form.get("notes")
        if not name or not species or not food or not feed_freq:
            error = "Enter required fields"
            return render_template("addpet.html", error=error)
        else:
            data = pets(session["user_id"], name, birthdate, species, sex, traits, food, feed_freq, vet, vet_num, env, picpath, pic, notes)
            db.session.add(data)
            db.session.commit()
            success = "Pet successfully added!"
            return redirect("/home")


@app.route("/home")
@login_required
def home():
    pet = db.session.query(pets).filter_by(user_id=session["user_id"]).all()
    return render_template("home.html", pet=pet)

@app.route("/view", methods=["POST"])
@login_required
def view():
    petid = request.form["view"]
    pet = db.session.query(pets).filter(pets.id == petid).all()
    med = db.session.query(meds).filter(meds.pet_id == petid).all()
    return render_template("viewpet.html", pet=pet, med=med)

# edit pet entry TODO
@app.route("/edit", methods=["GET","POST"])
@login_required
def edit():
    if request.method == "POST":
        edit_id = request.form["edit"]
        existing = db.session.query(pets).filter(pets.id==edit_id).first()
        pet = db.session.query(pets).filter_by(user_id=session["user_id"]).all()
        med = db.session.query(meds).filter_by(user_id=session["user_id"]).all()
        return render_template("editpet.html", existing=existing, pet=pet, med=med, )
    if request.method == "GET":
        pet = db.session.query(pets).filter_by(user_id=session["user_id"]).all()
        med = db.session.query(meds).filter_by(user_id=session["user_id"]).all()
        return render_template("editpet.html", pet=pet, med=med)

@app.route("/editsub", methods=["POST"])
@login_required
def editsub():
    if request.method == "POST":
        edit_id = request.form["edit"]
        # Update main entry
        name = request.form.get("name")
        birthdate = request.form.get("birthdate")
        if birthdate == "":
            birthdate = None
        species = request.form.get("species")
        sex = request.form.get("sex")
        traits = request.form.get("traits")
        food = request.form.get("food")
        feed_freq = request.form.get("feed_freq")
        vet = request.form.get("vet")
        vet_num = request.form.get("vet_num")
        env = request.form.get("env")
        update = db.session.query(pets).filter(pets.id == edit_id).first()
        update.name = name
        update.birthdate = birthdate
        update.traits = traits
        update.species = species
        update.sex = sex
        update.food = food
        update.feed_freq = feed_freq
        update.vet = vet
        update.vet_num = vet_num
        update.env = env
        
        update = db.session.query(meds).filter(meds.id == edit_id).first()

        db.session.commit()
        success = "Entry updated!"
        return redirect("/edit")

@app.route("/updatemed", methods=["POST"])
@login_required
def updatemed():
    # update medical
        edit_id2 = request.form["editmed"]
        weight = request.form.get("weight")
        if request.form.get("medstat") == "on":
            medstat = True
        else:
            medstat = False
        medication = request.form.get("medication")
        dosage = request.form.get("dosage")
        datestart = request.form.get("datestart")
        if datestart == "":
            datestart = None
        dateend = request.form.get("dateend")
        if dateend == "":
            dateend = None
        notes = request.form.get("notes")
        dateentry = request.form.get("dateentry")
        if dateentry == "":
            error = "Please enter required fields"
            return render_template("editpet.html", error=error)
        notes = request.form.get("notes")
        update = db.session.query(meds).filter(meds.id == edit_id2).first()
        update.weight = weight
        update.medstat = medstat
        update.medication = medication
        update.dosage = dosage
        update.datestart = datestart
        update.dateend = dateend
        update.notes = notes
        update.dateentry = dateentry
        db.session.commit()
        success = "Entry updated!"
        return redirect("/edit")

@app.route("/addmedical", methods=["POST"])
@login_required
def addmedical():
    # pet id
    edit_id = request.form["edit2"]
    weight = request.form.get("weight")

    if request.form.get("medstat") == "on":
        medstat = True
    else:
        medstat = False
    medication = request.form.get("medication")
    dosage = request.form.get("dosage")
    datestart = request.form.get("datestart")
    if datestart == "":
        datestart = None
    dateend = request.form.get("dateend")
    if dateend == "":
        dateend = None
    notes = request.form.get("notes")
    dateentry = request.form.get("dateentry")
    if dateentry == "":
        dateentry = None

    data = meds(session["user_id"], edit_id, weight, medstat, medication, dosage, datestart, dateend, notes, dateentry)
    db.session.add(data)
    db.session.commit()
    return redirect("/edit")
    
# delete pet entry 
@app.route("/delete", methods=["POST"])
@login_required
def deletep():
    del_id = request.form["delete"]
    del_ob = db.session.query(pets).filter(pets.id == del_id).first()
    db.session.delete(del_ob)
    db.session.commit()
    return redirect("/home")

# delete medical entry 
@app.route("/deletemed", methods=["POST"])
@login_required
def deletemed():
    del_id = request.form["delete"]
    del_ob = db.session.query(meds).filter(meds.id == del_id).first()
    db.session.delete(del_ob)
    db.session.commit()
    return redirect("/edit")

# share guest code
@app.route("/share")
@login_required
def share():
    guest = db.session.query(users).filter(users.id == session["user_id"]).first()
    return render_template("share.html", guest=guest)

# generate new guest pass
@app.route("/newguest", methods=["POST"])
@login_required
def newguest():
    newpass = guestp()
    update = db.session.query(users).filter(users.id == session["user_id"]).first()
    update.guest_pass = newpass
    db.session.commit()
    return redirect("/share")


# retrieve info for guest
@app.route("/guest", methods=["GET", "POST"])
def guest():
    if request.method == "GET":
        return render_template("guest.html")
    else:
        gpass = request.form.get("pass")
        if gpass == None:
            return redirect("/guest")
        
        else:
            # get user id by referencing against guest pass
            idkey = db.session.query(users).filter(users.guest_pass == gpass).first()
            if idkey == None:
                error = "Enter valid guest pass"
                return render_template("guest.html", error=error)
            #      db.session.query(pets).filter_by(user_id=session["user_id"]).all()
            pet = db.session.query(pets).filter_by(user_id = idkey.id).all()
            med = db.session.query(meds).filter_by(user_id = idkey.id).all()
            return render_template("guestview.html", pet=pet, med=med)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.debug = True
    app.run()