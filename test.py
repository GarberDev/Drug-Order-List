import pytest
from forms import (RegistrationForm, LoginForm, TimeOffRequestForm, BlacklistClientForm, EditBlacklistedClientForm,
                   CreatePostForm, CommentForm, FeatureSuggestionForm)
from app import app as flask_app, db, bcrypt
from models import User


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.create_all()
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client
    db.session.remove()
    db.drop_all()


@pytest.fixture
def session(client):
    with client.session_transaction() as sess:
        yield sess


def test_index(client):
    response = client.get('/')
    assert b'Login' in response.data


def test_login(client):
    # Add a test user
    hashed_password = bcrypt.hashpw(
        'testpassword'.encode('utf-8'), bcrypt.gensalt())
    test_user = User(username='testuser', password=hashed_password.decode('utf-8'), email='testuser@test.com',
                     first_name='Test', last_name='User')
    db.session.add(test_user)
    db.session.commit()

    # Test successful login
    response = client.post('/', data=dict(username='testuser',
                           password='testpassword'), follow_redirects=True)
    assert b'Logged in successfully!' in response.data

    # Test failed login
    response = client.post('/', data=dict(username='wronguser',
                           password='wrongpassword'), follow_redirects=True)
    assert b'Invalid username or password.' in response.data


def test_delete_time_off_request(client):
    response = client.get('/delete_time_off_request/1')
    assert response.status_code == 200


def test_manager_time_off_requests(client, session):
    session['username'] = 'test_username'
    response = client.get('/manager/time_off_requests')
    assert response.status_code == 200


def test_approve_time_off_request(client, session):
    session['username'] = 'test_username'
    response = client.post('/manager/approve_time_off_request/1')
    assert response.status_code == 302


def test_registration_form():
    form = RegistrationForm(
        username="test",
        password="password",
        email="test@gmail.com",
        first_name="First",
        last_name="Last"
    )
    assert form.validate() == True


def test_login_form():
    form = LoginForm(username="test", password="password")
    assert form.validate() == True


def test_time_off_request_form():
    form = TimeOffRequestForm(
        shift_coverage_date="2023-05-30",
        covering_user=1,
        reason='vacation',
        shift_time="09:00 - 17:00",
        request_acknowledged=True
    )
    assert form.validate() == True


def test_blacklist_client_form():
    form = BlacklistClientForm(
        client_name="Client Name",
        reason="Reason for blacklisting",
        blacklisting_person="Employee Name"
    )
    assert form.validate() == True


def test_edit_blacklisted_client_form():
    form = EditBlacklistedClientForm(
        client_name="Client Name",
        reason="Reason for blacklisting",
        blacklisting_person="Employee Name"
    )
    assert form.validate() == True


def test_create_post_form():
    form = CreatePostForm(content="This is a new post")
    assert form.validate() == True


def test_feature_suggestion_form():
    form = FeatureSuggestionForm(suggestion="This is a feature suggestion")
    assert form.validate() == True
