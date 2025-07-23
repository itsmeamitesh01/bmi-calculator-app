import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required, logout_user,
    UserMixin, current_user
)
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv  
load_dotenv()  # Load environment variables from .env file
# ------------------- App Config -------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bmi_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------- Models -------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bmis = db.relationship('BMIRecord', backref='user', lazy=True)

class BMIRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bmi = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ------------------- Login Loader -------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------- Routes -------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not all([name, email, password]):
            flash("Please fill in all fields.")
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.")
        return redirect(url_for('login'))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = None

    if request.method == "POST":
        try:
            system = request.form.get("system")
            weight = float(request.form.get("weight"))
            feet = int(request.form.get("feet"))
            inches = int(request.form.get("inches"))
        except (TypeError, ValueError):
            flash("Invalid input. Please enter valid numbers.")
            return redirect(url_for("dashboard"))

        # Height conversion
        if system == "imperial":
            height_in = feet * 12 + inches
            bmi = round((weight * 703) / (height_in ** 2), 2)
        else:  # metric
            height_m = feet * 0.3048 + inches * 0.0254
            bmi = round(weight / (height_m ** 2), 2)

        # Categorize BMI
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Healthy weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"

        result = f"{current_user.name}, your BMI is {bmi} and you are {category}."
        record = BMIRecord(bmi=bmi, category=category, user_id=current_user.id)
        db.session.add(record)
        db.session.commit()

    # Fetch last 5 BMI records
    records = BMIRecord.query.filter_by(user_id=current_user.id).order_by(
        BMIRecord.date.desc()).limit(5).all()

    return render_template("dashboard.html", result=result, records=records, name=current_user.name)

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 