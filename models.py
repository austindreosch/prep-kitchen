from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# from flask_bcrypt import Bcrypt

db = SQLAlchemy()
# bcrypt = Bcrypt()

# DO NOT MODIFY THIS FUNCTION


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """Users model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    subscribed = db.Column(db.Boolean, default=False)

    # songs = db.relationship('PlaylistSong', backref="songs")


class Plan(db.Model):
    """Plans model."""
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    price = db.Column(db.Integer, nullable=False)
    serving_count = db.Column(db.Integer, nullable=False)
    meal_count = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)


class Order(db.Model):
    """Orders model."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow()
    )
    meal_id1 = db.Column(db.Integer, nullable=False)
    meal_id2 = db.Column(db.Integer, nullable=False)
    meal_id3 = db.Column(db.Integer, nullable=False)
    meal_id4 = db.Column(db.Integer)
    meal_id5 = db.Column(db.Integer)
