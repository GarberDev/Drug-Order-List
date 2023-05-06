from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import psycopg2
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Client, MedicationToBeOrdered, MedicationOnOrder, OrderReceived, TimeOffRequest
from datetime import date
from datetime import datetime
import requests

from forms import RegistrationForm, LoginForm, TimeOffRequestForm, EditBlacklistedClientForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///drug_list'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'
OPENFDA_API_BASE_URL = "https://api.fda.gov/drug/"

connect_db(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            session["username"] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('medications', username=user.username))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form,)
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
################# medication routes#####################


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


######## function to fetch OpenFDA API data###############
def get_openfda_data(med_name):
    print(med_name)
    response = requests.get(
        f"{OPENFDA_API_BASE_URL}label.json?search={med_name}")
    print(response)
    data = response.json()
    print(data)
    if "results" in data:
        return data["results"][0]
    else:
        return None


@app.route("/medications/details")
def get_medication_details():
    medication = request.args.get('name', None)
    if medication:
        openfda_data = get_openfda_data(medication)
        return render_template("medication_details.html", medication=medication, openfda_data=openfda_data)
    else:
        flash('No medication name provided.', 'danger')
        return redirect(url_for('medications'))


###################### reports##########################


@app.route("/reports")
def reports():
    orders_received = OrderReceived.query.all()
    return render_template("reports.html", orders_received=orders_received)

############################ time off request#######################


@app.route('/time_off_request', methods=['GET', 'POST'])
def time_off_request():
    form = TimeOffRequestForm()
    form.covering_user.choices = [(u.id, u.username) for u in User.query.all()]

    if form.validate_on_submit():
        user = User.query.filter_by(username=session['username']).first()
        time_off_request = TimeOffRequest(
            user_id=user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            covering_user_id=form.covering_user.data
        )
        db.session.add(time_off_request)
        db.session.commit()
        flash('Time off request submitted.', 'success')
        return redirect(url_for('show_time_off_requests'))

    return render_template('time_off_request.html', form=form)


@app.route('/time_off_request/edit/<int:time_off_request_id>', methods=['GET'])
def show_edit_time_off_request(time_off_request_id):
    time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)
    current_user = User.query.filter_by(username=session['username']).first()
    return render_template('edit_time_off_request.html', current_user=current_user, time_off_request=time_off_request)


@app.route('/time_off_request/edit/<int:time_off_request_id>', methods=['POST'])
def edit_time_off_request(time_off_request_id):
    time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    time_off_request.start_date = datetime.strptime(
        start_date, "%Y-%m-%d").date()
    time_off_request.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    db.session.commit()

    return redirect(url_for('show_time_off_requests'))


@app.route('/time_off_requests', methods=['GET'])
def show_time_off_requests():
    current_user = User.query.filter_by(username=session['username']).first()
    user_time_off_requests = TimeOffRequest.query.filter_by(
        user_id=current_user.id).all()
    covered_time_off_requests = TimeOffRequest.query.filter_by(
        covering_user_id=current_user.id).all()

    return render_template('show_time_off_requests.html', user_time_off_requests=user_time_off_requests, covered_time_off_requests=covered_time_off_requests, current_user=current_user)

################################## blacklisted clients#######################


@app.route('/blacklisted_clients')
def show_blacklisted_clients():
    # Retrieve blacklisted clients from the database
    blacklisted_clients = Client.query.filter(
        Client.is_blacklisted == True).all()

    return render_template('blacklisted_clients.html', blacklisted_clients=blacklisted_clients)


@app.route('/edit_blacklisted_client/<int:client_id>', methods=['GET', 'POST'])
def edit_blacklisted_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = EditBlacklistedClientForm()

    if form.validate_on_submit():
        client.name = form.client_name.data
        client.blacklist_reason = form.reason.data
        client.blacklisting_person = form.blacklisting_person.data
        db.session.commit()
        flash('Blacklisted client has been updated.', 'success')
        return redirect(url_for('show_blacklisted_clients'))

    form.client_name.data = client.name
    form.reason.data = client.blacklist_reason
    form.blacklisting_person.data = client.blacklisting_person
    return render_template('edit_blacklisted_client.html', form=form, client=client)


if __name__ == "__main__":
    app.run(debug=True)
