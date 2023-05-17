from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()


def connect_db(app):

    # Retrieve the DB URL from environment variables
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://drug_list_user:6OloIXwOMDOgHVmjWwQatrARDlGnwxwn@dpg-chi7iql269vf5qb7gsn0-a/drug_list'
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    # with app.app_context():
    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    is_manager = db.Column(db.Boolean, default=False, nullable=False)


class MedicationToBeOrdered(db.Model):
    __tablename__ = "medication_to_be_ordered"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    date_requested = db.Column(db.Date, nullable=False)
    backordered = db.Column(db.Boolean, default=False, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref='medications_on_order')


class MedicationOnOrder(db.Model):
    __tablename__ = "medication_on_order"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    date_order_placed = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship(
        'User', backref='medications_on_order_backref', lazy=True)  # Change backref name here


class OrderReceived(db.Model):
    __tablename__ = "order_received"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    date_received = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    received_by = db.Column(db.String(30), nullable=False)


class TimeOffRequest(db.Model):
    __tablename__ = 'time_off_request'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref(
        'time_off_requests', lazy=True))
    shift_time = db.Column(db.String(120), nullable=False)
    shift_coverage_date = db.Column(db.Date, nullable=False)
    covering_user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=True)
    covering_user = db.relationship('User', foreign_keys=[
                                    covering_user_id], backref=db.backref('covered_requests', lazy=True))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reason = db.Column(db.String, nullable=False)
    request_acknowledged = db.Column(db.Boolean, default=False, nullable=False)
    manager_approval = db.Column(db.Boolean, nullable=True)


class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(256))
    blacklisting_person = db.Column(db.String(128))


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
