import logging
import os
import pandas as pd
import requests
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from sqlite3 import IntegrityError, InternalError, Error


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
    user_id = db.Column(db.Integer, unique=True, nullable=True)
    # lat = db.Column(db.Float, nullable=True)
    # lon = db.Column(db.Float, nullable=True)
    city = db.Column(db.String, db.ForeignKey('cities.name'))
    # weather = db.relationship("WeatherData")

    # weather_id = db.Column(db.Integer, db.ForeignKey('weather_data.id'))


class City(db.Model):
    __tablename__: str = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    # name = db.Column(db.String, primary=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    users = db.relationship('User')
    weather = db.relationship('WeatherData')
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class WeatherData(db.Model):
    __tablename__: str = 'weather_data'

    daytime = db.Column(db.DateTime, primary_key=True)
    # city = db.Column(db.String, nullable=False)
    sunrise = db.Column(db.DateTime, nullable=True)
    sunset = db.Column(db.DateTime, nullable=True)
    temp = db.Column(db.Float, nullable=True)
    dew_point = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    probability = db.Column(db.Integer, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_gust = db.Column(db.Float, nullable=True)
    # city_id = db.relationship('User', back_populates='weather')
    city = db.Column(db.String, db.ForeignKey('cities.name'))

# with app.app_context():
#     db.create_all()


################### CITY ########################
def city_add(name, lat, lon):
    cty = City(name=name, lat=lat, lon=lon)
    with app.app_context():
        try:
            db.session.add(cty)
        except IntegrityError as e:
            logging.error(msg="Exception while adding city:", exc_info=e)
        finally:
            db.session.commit()


def city_get_coord(name):
    with app.app_context():
        try:
            city = db.get_or_404(City, name)
        except Error as e:
            logging.warning(f"{name} not found in cities: \n{e}")
            return False
        return city.lat, city.lon


def city_get_name(lat, lon):
    with app.app_context():
        try:
            city = db.get_or_404(City, (lat, lon))
        except Error as e:
            logging.warning(f"{lat}, {lon} not found in cities: \n{e}")
            return False
        return city.name


def city_list():
    with app.app_context():
        # users = db.session.execute(db.select(User).order_by(User.name))# .scalars()
        cty = City.query.all()
    return cty


##################### USER ######################
@app.route("/users")
def user_list():
    with app.app_context():
        # users = db.session.execute(db.select(User).order_by(User.name))# .scalars()
        users = User.query.all()
    return users


@app.route("/new", methods=["GET", "POST"])
def user_add(name, user_id, city):
    user = User(
        name=name,
        user_id=user_id,
        city=city,

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
        try:
            user = db.get_or_404(User, user_id)
        except Exception:
            return None
        return user


@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
def user_delete(user_id):
    with app.app_context():
        user = db.get_or_404(User, user_id)
        db.session.delete(user)
        db.session.commit()
    return "success"


####################### WEATHER ######################
def new_weather_data(weather_df: pd.DataFrame, city):
    # for row in weather_df.iterrows():
    #     weather = WeatherData(
    #         daytime=row.dt,
    #         city=city,
    #         sunrise=row.sunrise,
    #         sunset=row.sunset,
    #         temp=row.temp,
    #         dew_point=row.dew_point,
    #         humidity=row.humidity,
    #         probability=row.probability,
    #         wind_speed=row.wind_speed,
    #         wind_gust=row.wind_gust,
    #         # lat=weather_df.weather_dflat,
    #         # lon=weather_df.lon,
    #     )
    with app.app_context():
        weather_df.to_sql(name=city, con=db.engine)
        # db.session.add(weather)
        db.session.commit()
    return "success??"


port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
