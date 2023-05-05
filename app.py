from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import psycopg2
from psycopg2 import IntegrityError
from models import db, connect_db, User, MedicationToBeOrdered, MedicationOnOrder, OrderReceived
from datetime import date
from models import MedicationToBeOrdered, MedicationOnOrder, OrderReceived

import requests

from forms import RegistrationForm, LoginForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///drug_list'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'
OPENFDA_API_BASE_URL = "https://api.fda.gov/drug/"

connect_db(app)


@app.route('/')
def index():
    register_url = url_for('register')
    login_url = url_for('login')
    if 'username' in session:
        form = LoginForm()
        username = User.query.filter_by(username=form.username.data).first()

        return redirect(url_for('medications'))
    else:
        username = None
    return render_template('index.html', register_url=register_url, login_url=login_url, username=username)


################# user routes#####################

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data, email=form.email.data,
                    first_name=form.first_name.data, last_name=form.last_name.data)
        try:
            db.session.add(user)
            db.session.commit()
            session["username"] = user.username
            flash('User registered successfully!', 'success')
            return redirect(url_for('medications', username=user.username))
        except IntegrityError:
            db.session.rollback()
            flash('Username or Email is already taken.', 'danger')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            session["username"] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('medications', username=user.username))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route('/users/<username>')
def user_detail(username):
    if 'username' not in session or session['username'] != username:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get_or_404(username)

    return render_template('user_detail.html', user=user,)


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'username' not in session or session['username'] != username:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return redirect('/')


# @app.route("/")
# def root():
#     """Render homepage."""
#     return render_template("medications.html")

################# medication list routes#####################


@app.route("/medications")
def medications():
    meds_to_be_ordered = MedicationToBeOrdered.query.all()
    meds_on_order = MedicationOnOrder.query.all()
    orders_received = OrderReceived.query.all()
    return render_template("medications.html", meds_to_be_ordered=meds_to_be_ordered, meds_on_order=meds_on_order, orders_received=orders_received)


@app.route("/medications/to-be-ordered", methods=["POST"])
def add_medication_to_be_ordered():
    if 'username' not in session:
        flash('You must be logged in to add a medication.', 'danger')
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()

    name = request.form["name"]
    date_requested = date.today()
    quantity = request.form["quantity"]
    backordered = request.form.get("backordered") == "on"

    new_medication = MedicationToBeOrdered(
        name=name, date_requested=date_requested, backordered=backordered, quantity=quantity, user_id=current_user.id)
    db.session.add(new_medication)
    db.session.commit()

    return redirect("/medications")


@app.route("/medications/on-order/<int:med_id>", methods=["POST"])
def move_to_on_order(med_id):
    if 'username' not in session:
        flash('You must be logged in to place a medication on order.', 'danger')
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()

    # Update the variable name when querying the MedicationToBeOrdered model
    med_to_be_ordered = MedicationToBeOrdered.query.get_or_404(med_id)

    med_on_order = MedicationOnOrder(
        name=med_to_be_ordered.name,
        date_order_placed=date.today(),
        quantity=med_to_be_ordered.quantity,
        user_id=current_user.id
    )
    db.session.add(med_on_order)
    db.session.delete(med_to_be_ordered)
    db.session.commit()

    return redirect("/medications")


@app.route("/medications/received/<int:med_id>", methods=["POST"])
def move_to_received(med_id):
    med_on_order = MedicationOnOrder.query.get_or_404(med_id)

    user = User.query.filter_by(username=session['username']).first()

    received_by = user.first_name

    order_received = OrderReceived(
        name=med_on_order.name, date_received=date.today(), quantity=med_on_order.quantity, received_by=received_by)
    db.session.add(order_received)
    db.session.delete(med_on_order)
    db.session.commit()

    return redirect("/medications")


################# medication detail routes#####################


@app.route("/medications/<int:med_id>")
def show_medication_details(med_id):
    medication = MedicationToBeOrdered.query.get_or_404(med_id)
    openfda_data = get_openfda_data(medication.name)
    return render_template("medication_details.html", medication=medication, openfda_data=openfda_data)


# Add the function to fetch OpenFDA API data
def get_openfda_data(med_name):
    print(med_name)
    response = requests.get(
        f"{OPENFDA_API_BASE_URL}label.json?search=dosage_forms_and_strengths:{med_name}")
    print(response)
    data = response.json()
    print(data)
    if "results" in data:
        return data["results"][0]
    else:
        return None


# @app.route("/medications/new")
# def new_medication():
#     """Display the medication details form for a new medication."""
#     medication = MedicationToBeOrdered.query.order_by(
#         MedicationToBeOrdered.id.desc()).first()
#     return redirect(url_for("medication_details", med_id=medication.id))


if __name__ == "__main__":
    app.run(debug=True)
