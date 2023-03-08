import os
import pprint

import requests
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


# https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/
app = Flask(__name__)
##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__: str = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    # weather_data = Mapped[List["WeatherData"]] = relationship(back_populates='user')


class WeatherData(db.Model):
    __tablename__: str = 'weather_data'

    daytime = db.Column(db.Integer, primary_key=True)
    sunrise = db.Column(db.Integer, nullable=True)
    sunset = db.Column(db.Integer, nullable=True)
    temp = db.Column(db.Integer, nullable=True)
    dew_point = db.Column(db.Integer, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    probability = db.Column(db.Integer, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_gust = db.Column(db.Float, nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    # user = Mapped["User"] = relationship(back_polulates='weather_data')


with app.app_context():
    db.create_all()


@app.route('/')
def index(word):
    return redirect(url_for(user_list))


@app.route("/users")
def user_list():
    with app.app_context():
        # users = db.session.execute(db.select(User).order_by(User.name))# .scalars()
        users = User.query.all()
    return users


@app.route("/new", methods=["GET", "POST"])
def user_add(name="None", user_id="None", lat=0, lon=0):
    user = User(
        name=name,
        user_id=user_id,
        lat=lat,
        lon=lon,
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()
    return "success??"


@app.route("/user/<int:id>")
def user_detail(user_id):
    with app.app_context():
        # stmt = select(User).where(User.user_id == user_id)
        # user = db.session.execute(stmt)
        user = db.get_or_404(User, user_id)

    return user


@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
def user_delete(user_id):
    with app.app_context():
        user = db.get_or_404(User, user_id)
        db.session.delete(user)
        db.session.commit()
    return "success"


port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=port)
