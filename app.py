from flask import Flask, abort, request, render_template, redirect, url_for, flash, session
import psycopg2
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, Client, MedicationToBeOrdered, MedicationOnOrder, OrderReceived, TimeOffRequest, Post, Comment
from datetime import date
from hidden import password, mail_username, duplicate_email
import bcrypt
import requests
from flask_mail import Message, Mail
# from flask_migrate import Migrate
from forms import FeatureSuggestionForm, RegistrationForm, LoginForm, TimeOffRequestForm, EditBlacklistedClientForm, BlacklistClientForm, CreatePostForm, CommentForm
from flask.cli import FlaskGroup
from flask_wtf.csrf import CSRFProtect


# def create_app():
#     flask_app = Flask(__name__)
#     csrf.init_app(flask_app)

#     return flask_app


flask_app = Flask(__name__)

# cli = FlaskGroup(flask_app)
# flask_app.cli.add_command(cli)


flask_app.secret_key = 'your_secret_key'

csrf = CSRFProtect(flask_app)


# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///drug_list'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.config['SECRET_KEY'] = 'secret'
flask_app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
flask_app.config['MAIL_PORT'] = 587
flask_app.config['MAIL_USE_TLS'] = True
flask_app.config['MAIL_USERNAME'] = mail_username  # Your email address
flask_app.config['MAIL_PASSWORD'] = password     # Your email password

mail = Mail(flask_app)

OPENFDA_API_BASE_URL = "https://api.fda.gov/drug/"

connect_db(flask_app)

with flask_app.app_context():
    db.create_all()

# migrate = Migrate(flask_app, db)
# migrate.init_app(flask_app, db)


@flask_app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.checkpw(form.password.data.encode('utf-8'), user.password.encode('utf-8')):
            session["username"] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('medications', username=user.username))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form,)
################# user routes#####################


@flask_app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password with bcrypt
        hashed_password = bcrypt.hashpw(
            form.password.data.encode('utf-8'), bcrypt.gensalt())

        user = User(username=form.username.data, password=hashed_password.decode('utf-8'), email=form.email.data,
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


@flask_app.route('/logout')
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@flask_app.route('/users/<username>')
def user_detail(username):
    print(username)
    if 'username' not in session or session['username'] != username:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    print(username)
    user = User.query.get_or_404(username)
    print(user)

    return render_template('user_detail.html', user=user)


@flask_app.route('/users/<username>/delete', methods=['POST'])
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


@flask_app.route("/medications")
def medications():
    meds_to_be_ordered = MedicationToBeOrdered.query.all()
    meds_on_order = MedicationOnOrder.query.all()
    orders_received = OrderReceived.query.all()
    joke = get_joke()
    return render_template("medications.html", joke=joke, meds_to_be_ordered=meds_to_be_ordered, meds_on_order=meds_on_order, orders_received=orders_received)


@flask_app.route("/medications/to-be-ordered", methods=["POST"])
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


@flask_app.route("/medications/on-order/<int:med_id>", methods=["POST"])
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


@flask_app.route("/medications/received/<int:med_id>", methods=["POST"])
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

@flask_app.route("/medications/<int:med_id>")
def show_medication_details(med_id):
    medication = MedicationToBeOrdered.query.get(med_id)
    med_on_order = None
    if medication is None:
        medication = MedicationOnOrder.query.get(med_id)
        med_on_order = medication
    openfda_data = get_openfda_data(medication.name)
    return render_template("medication_details.html", medication=medication, openfda_data=openfda_data, med_on_order=med_on_order,)

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


@flask_app.route("/medications/details")
def get_medication_details():
    medication = request.args.get('name', None)
    if medication:
        openfda_data = get_openfda_data(medication)
        return render_template("medication_details.html", medication=medication, openfda_data=openfda_data)
    else:
        flash('No medication name provided.', 'danger')
        return redirect(url_for('medications'))


###################### reports##########################


@flask_app.route("/reports")
def reports():
    orders_received = OrderReceived.query.all()
    joke = get_joke()
    return render_template("reports.html", orders_received=orders_received, joke=joke)

############################ time off request#######################


@flask_app.route('/time_off_request', methods=['GET', 'POST'])
def time_off_request():
    if 'username' not in session:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('index'))

    form = TimeOffRequestForm()
    form.covering_user.choices = [(u.id, u.username) for u in User.query.all()]
    current_user = User.query.filter_by(username=session['username']).first()
    if form.validate_on_submit():
        user = User.query.filter_by(username=session['username']).first()
        time_off_request = TimeOffRequest(
            user_id=user.id,
            shift_coverage_date=form.shift_coverage_date.data,
            covering_user_id=form.covering_user.data,
            shift_time=form.shift_time.data,
            reason=form.reason.data,
            request_acknowledged=form.request_acknowledged.data,
            manager_approval=None
        )
        db.session.add(time_off_request)
        db.session.commit()
        flash('Time off request submitted.', 'success')
        return redirect(url_for('show_time_off_requests'))
    joke = get_joke()
    return render_template('time_off_request.html', form=form, current_user=current_user, joke=joke)


######################### edit time off request####################

@flask_app.route('/time_off_request/edit/<int:time_off_request_id>', methods=['GET'])
def show_edit_time_off_request(time_off_request_id):
    time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)
    form = TimeOffRequestForm(obj=time_off_request)
    form.covering_user.choices = [(u.id, u.username) for u in User.query.all()]
    current_user = User.query.filter_by(username=session['username']).first()
    return render_template('edit_time_off_request.html', current_user=current_user, time_off_request=time_off_request, form=form)


@flask_app.route('/time_off_request/edit/<int:time_off_request_id>', methods=['GET', 'POST'])
def edit_time_off_request(time_off_request_id):
    time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)
    form = TimeOffRequestForm(obj=time_off_request)
    form.covering_user.choices = [(u.id, u.username) for u in User.query.all()]
    current_user = User.query.filter_by(username=session['username']).first()

    if form.validate_on_submit():
        print("Form submitted and passed validation")
        time_off_request.shift_coverage_date = form.shift_coverage_date.data
        time_off_request.covering_user_id = form.covering_user.data
        time_off_request.reason = form.reason.data
        time_off_request.request_acknowledged = form.request_acknowledged.data
        time_off_request.manager_approval = form.manager_approval.data if current_user.is_manager else None
        time_off_request.shift_time = form.shift_time.data

        db.session.commit()
        flash('Time off request updated.', 'success')
        return redirect(url_for('show_time_off_requests'))
    else:
        print(form.errors)
    return render_template('edit_time_off_request.html', form=form, current_user=current_user, time_off_request=time_off_request)


@flask_app.route('/time_off_requests', methods=['GET'])
def show_time_off_requests():
    current_user = User.query.filter_by(username=session['username']).first()
    user_time_off_requests = TimeOffRequest.query.filter_by(
        user_id=current_user.id).all()
    covered_time_off_requests = TimeOffRequest.query.filter_by(
        covering_user_id=current_user.id).all()

    return render_template('show_time_off_requests.html', user_time_off_requests=user_time_off_requests, covered_time_off_requests=covered_time_off_requests, current_user=current_user)


################################## delete time off request###############################

@flask_app.route('/delete_time_off_request/<int:time_off_request_id>', methods=['GET'])
def delete_time_off_request(time_off_request_id):
    time_off_request = TimeOffRequest.query.get(time_off_request_id)
    db.session.delete(time_off_request)
    db.session.commit()
    flash('Time off request deleted.')
    return redirect(url_for('show_time_off_requests'))

############################# managers#############################


@flask_app.route('/manager/time_off_requests')
def manager_time_off_requests():
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user.is_manager:
        abort(403)
    time_off_requests = TimeOffRequest.query.filter_by(
        manager_approval=False).all()
    return render_template('manager_time_off_requests.html', time_off_requests=time_off_requests)


@flask_app.route('/manager/approve_time_off_request/<int:time_off_request_id>', methods=['POST'])
def approve_time_off_request(time_off_request_id):
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user.is_manager:
        abort(403)
    time_off_request = TimeOffRequest.query.get(time_off_request_id)
    time_off_request.manager_approval = True
    db.session.commit()
    return redirect(url_for('manager_time_off_requests'))

################################## blacklisted clients#######################


@flask_app.route('/blacklisted_clients')
def show_blacklisted_clients():
    # Retrieve blacklisted clients from the database
    blacklisted_clients = Client.query.filter(
        Client.is_blacklisted == True).all()
    joke = get_joke()
    return render_template('blacklisted_clients.html', blacklisted_clients=blacklisted_clients, joke=joke)


@flask_app.route('/edit_blacklisted_client/<int:client_id>', methods=['GET', 'POST'])
def edit_blacklisted_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = EditBlacklistedClientForm()

    if form.validate_on_submit():
        client.name = form.client_name.data
        client.reason = form.reason.data
        client.blacklisting_person = form.blacklisting_person.data
        db.session.commit()
        flash('Blacklisted client has been updated.', 'success')
        return redirect(url_for('show_blacklisted_clients'))

    form.client_name.data = client.name
    form.reason.data = client.reason
    form.blacklisting_person.data = client.blacklisting_person
    return render_template('edit_blacklisted_client.html', form=form, client=client)


@flask_app.route('/add_blacklisted_client', methods=['GET', 'POST'])
def add_blacklisted_client():
    form = BlacklistClientForm()

    if form.validate_on_submit():
        new_client = Client(
            name=form.client_name.data,
            reason=form.reason.data,
            blacklisting_person=form.blacklisting_person.data,
            is_blacklisted=True
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Client added to the blacklist.', 'success')
        return redirect(url_for('show_blacklisted_clients'))

    return render_template('add_blacklisted_client.html', form=form)

########################### Messageboar##############################


@flask_app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        if 'username' not in session:
            flash('You must be logged in to create a post.', 'danger')
            return redirect(url_for('login'))

        content = request.form['content']
        user = User.query.filter_by(username=session['username']).first()
        post = Post(content=content, user_id=user.id)
        db.session.add(post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('posts'))
    joke = get_joke()
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('posts.html', posts=posts, joke=joke)


@flask_app.route('/posts/<int:post_id>/comments', methods=['GET', 'POST'])
def comments(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        if 'username' not in session:
            flash('You must be logged in to comment on a post.', 'danger')
            return redirect(url_for('login'))

        content = request.form['content']
        user = User.query.filter_by(username=session['username']).first()
        comment = Comment(content=content, user_id=user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()

        flash('Comment added successfully!', 'success')
        return redirect(url_for('comments', post_id=post_id))

    comments = Comment.query.filter_by(
        post_id=post.id).order_by(Comment.timestamp.desc()).all()

    return render_template('comments.html', post=post, comments=comments)


@flask_app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = CreatePostForm()
    current_user = User.query.filter_by(username=session['username']).first()
    if form.validate_on_submit():
        post = Post(content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('posts'))
    return render_template('create_post.html', form=form)


@flask_app.route('/post/<int:post_id>/create_comment', methods=['GET', 'POST'])
def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('create_comment.html', form=form, post=post)


@flask_app.route('/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        flash('You must be logged in to delete a post.', 'danger')
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    user = User.query.filter_by(username=session['username']).first()

    if post.user_id != user.id:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('posts'))

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('posts'))

############################ add api's to messageboard######################


@flask_app.route('/joke')
def get_joke():
    url = 'https://icanhazdadjoke.com/'
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    joke = response.json()['joke']
    return render_template('joke.html', joke=joke)
########################### weather#######################


@flask_app.route('/weather')
def get_weather(zip_code):
    zip_code = request.args.get('zip')
    if not zip_code:
        return {'error': 'No zip code provided'}
    ###################### google geocoding api###################

    from hidden import GOOGLE_API_KEY

    # Use Google Geocoding API to get latitude and longitude
    geo_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&key={GOOGLE_API_KEY}'
    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()

    if geo_data['status'] != 'OK':
        return {'error': 'Invalid zip code'}

    location = geo_data['results'][0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']

    # latitude = 10
    # longitude = 80

##################################### forecast################################
    url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,apparent_temperature,precipitation_probability,relativehumidity_2m,windspeed_10m'
    response = requests.get(url)
    weather_data = response.json()
    print(weather_data)
######### def weather_info##########
    weather_info = {
        'weather_data': None,
        'current_temp': None,
        'high_temp': None,
        'low_temp': None,
        'humidity': None,
        'wind_speed_mph': None,
        'precipitation': None
    }
############ convert to fahrenheit##############
    temperatures_celsius = weather_data['hourly']['temperature_2m']
    temperatures_fahrenheit = [round((temp * 9/5) + 32, 1)
                               for temp in temperatures_celsius]
    weather_data['hourly']['temperature_2m'] = temperatures_fahrenheit

    current_temp = weather_data['hourly']['temperature_2m'][0]
    high_temp = max(weather_data['hourly']['temperature_2m'])
    low_temp = min(weather_data['hourly']['temperature_2m'])
    humidity = weather_data['hourly']['relativehumidity_2m'][0]
    wind_speed_mph = round(
        weather_data['hourly']['windspeed_10m'][0] * 2.23694, 1)
    precipitation = weather_data['hourly']['precipitation_probability'][0]
############### set variables################
    weather_info = {
        'weather_data': weather_data,
        'current_temp': current_temp,
        'high_temp': high_temp,
        'low_temp': low_temp,
        'humidity': humidity,
        'wind_speed_mph': wind_speed_mph,
        'precipitation': precipitation
    }

    return weather_info

##################### suggestions#######################


@flask_app.route('/suggest_feature', methods=['GET', 'POST'])
def suggest_feature():
    form = FeatureSuggestionForm()
    if form.validate_on_submit():
        msg = Message('Feature Suggestion',
                      sender=('Feature Suggestion',
                              duplicate_email),
                      recipients=[duplicate_email])
        msg.body = f'Suggestion: {form.suggestion.data}'
        mail.send(msg)

        flash('Feature suggestion submitted. Thank you!', 'success')
        return redirect(url_for('medications'))

    return render_template('suggest_feature.html', form=form)

####################### weatherpage#######################


@flask_app.route('/display_weather', methods=['GET', 'POST'])
def display_weather():

    zip_code = request.args.get('zip')
    if zip_code:
        weather_info = get_weather(zip_code)
    else:
        weather_info = {
            'weather_data': None,
            'current_temp': None,
            'high_temp': None,
            'low_temp': None,
            'humidity': None,
            'wind_speed_mph': None,
            'precipitation': None
        }
    current_temp = weather_info['current_temp']
    high_temp = weather_info['high_temp']
    low_temp = weather_info['low_temp']
    humidity = weather_info['humidity']
    wind_speed_mph = weather_info['wind_speed_mph']
    precipitation = weather_info['precipitation']
    joke = get_joke()
    return render_template('weather.html', joke=joke, current_temp=current_temp, high_temp=high_temp, low_temp=low_temp, humidity=humidity, wind_speed_mph=wind_speed_mph, precipitation=precipitation)


if __name__ == "__main__":
    flask_app.run(debug=True)
