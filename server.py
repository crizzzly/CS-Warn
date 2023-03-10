import os
import pprint

import requests
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, relationship

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
    city = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    # weather_id = db.Column(db.Integer, db.ForeignKey('weather_data.id'))


# class City(db.Model):
#     __tablename__ = "cities"
#
#     id = db.Column(db.Integer, primary=True)
#     name = db.Column(db.String, nullable=False)
#     lat = db.Column(db.Float, nullable=False)
#     lon = db.Column(db.Float, nullable=False)


class WeatherData(db.Model):
    __tablename__: str = 'weather_data'

    daytime = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String, nullable=False)
    sunrise = db.Column(db.Integer, nullable=True)
    sunset = db.Column(db.Integer, nullable=True)
    temp = db.Column(db.Integer, nullable=True)
    dew_point = db.Column(db.Integer, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    probability = db.Column(db.Integer, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_gust = db.Column(db.Float, nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    # users = db.relationship("WeatherData", backref='users')


with app.app_context():
    db.create_all()

################### CITY ########################



##################### USER ######################
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
def user_add(name="None", user_id="None", city="None", lat=0, lon=0):
    user = User(
        name=name,
        user_id=user_id,
        city=city,
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

####################### WEATHER ######################
def new_weather_data(weather_df):
    weather = WeatherData(
        daytime=weather_df.dt,
        city=weather_df.city,
        sunrise=weather_df.sunrise,
        sunset=weather_df.sunset,
        temp=weather_df.temp,
        dew_point=weather_df.dew_point,
        humidity=weather_df.humidity,
        probability=weather_df.probability,
        wind_speed=weather_df.wind_speed,
        wind_gust=weather_df.wind_gust,
        lat=weather_df.lat,
        lon=weather_df.lon,
        user=db.relationship("WeatherData", backref='users')
    )
    with app.app_context():
        db.session.add(weather)
        db.session.commit()
    return "success??"


port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
