#!/usr/bin/env python3.11
import logging
import os
from sqlite3 import IntegrityError, Error
from typing import Any, Iterator

import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pandas import DataFrame
from sqlalchemy.exc import OperationalError

# https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/
# https://docs.sqlalchemy.org/en/20/index.html
# https://github.com/python-telegram-bot/python-telegram-bot/wiki

# TODO: Instead of manually handling a database to store data, consider implementing
#  a subclass of BasePersistence. This allows you to simply pass an instance of that
#  subclass to the Updater/Dispatcher and let PTB handle the loading,
#  updating & storing of the data!
#  https://github.com/python-telegram-bot/v13.x-wiki/wiki/Making-your-bot-persistent

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
    city = db.Column(db.String, db.ForeignKey('cities.name'))
    # weather = db.relationship("Weather")

    # weather_id = db.Column(db.Integer, db.ForeignKey('weather_data.id'))

# class Base(db.Model):
#     pass
# # note for a Core table, we use the sqlalchemy.Column construct,
# # not sqlalchemy.orm.mapped_column
# association_table = db.Table(
#     "association_table",
#     Base.metadata,
#     # db.Column("left_id", db.ForeignKey("left_table.id")),
#     db.Column("city_id", db.ForeignKey("cities.id")),
#     db.Column("weather_id", db.ForeignKey("weather_data.id")),
# )


class City(db.Model):
    __tablename__: str = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    # name = db.Column(db.String, primary=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    users = db.relationship('User')



class Weather(db.Model):
    __tablename__: str = 'weather_data'
    daytime = db.Column(db.DateTime, primary_key=True)
    # city_name = db.Column(db.String, nullable=False)
    sunrise = db.Column(db.DateTime, nullable=True)
    sunset = db.Column(db.DateTime, nullable=True)
    temp = db.Column(db.Float, nullable=True)
    dew_point = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    probability = db.Column(db.Integer, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_gust = db.Column(db.Float, nullable=True)
    # city_name: db.Mapped["City"] = db.relationship(back_populates="weather_data")



with app.app_context():
    db.create_all()


################### CITY ########################
def city_add(name, lat, lon):
    cty = City(name=name, lat=lat, lon=lon)
    with app.app_context():
        try:
            db.session.add(cty)
            db.session.commit()
        except IntegrityError as e:
            logging.error(msg="server.py: Exception while adding city_name:", exc_info=e)



def city_get_coord(name):
    with app.app_context():
        try:
            # city = db.get_or_404(City, name)
            city = City.query.filter_by(name=name).one()
        except Error as e:
            logging.warning(f"server.py: {name} not found in cities: \n{e}")
            return False
        else:
            return city.lat, city.lon


def city_get_name(lat, lon):
    with app.app_context():
        try:
            # city = db.get_or_404(City, (lat, lon))
            city = City.query.filter_by(lat=lat, lon=lon).all()
        except Error as e:
            logging.exception(f"server.py: {lat}, {lon} not found in cities: \n", e)
            return False
        else:
            return city.name


def city_list():
    with app.app_context():
        # users = db.session.execute(db.select(User).order_by(User.name))# .scalars()
        try:
            cty = City.query.all()
        except Error as e:
            logging.exception("server.py: Exception in server.py - city_list\ntrying to query all cities", e)
    return cty


##################### USER ######################
@app.route("/users")
def user_list():
    with app.app_context():
        # users = db.session.execute(db.select(User).order_by(User.name))# .scalars()
        try:
            users = User.query.all()
        except Error as e:
            logging.exception("Exception while trying to query all users", e)
    return users


@app.route("/new", methods=["GET", "POST"])
def user_add(name, user_id, city):
    user = User(
        name=name,
        user_id=user_id,
        city=city,

    )
    with app.app_context():
        try:
            db.session.add(user)
            db.session.commit()
        except Error as e:
            logging.exception("Exception in server.py - user_add while trying to add new user", e)



@app.route("/user/<int:id>")
def user_detail(user_id):
    with app.app_context():
        # stmt = select(User).where(User.user_id == user_id)
        # user = db.session.execute(stmt)
        try:
            # user = db.get_or_404(User, user_id)
            user = User.query.filter_by(user_id=user_id).all()
        except Error as e:
            logging.exception(f"server.py: Exception in 'user_detail'\n"
                              f"Exception while trying to get user by id {user_id}", e)
            return False
        else:
            logging.info(f"server.py: Got user details from {user[0].name}")
            return user


@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
def user_delete(user_id: int):
    with app.app_context():
        try:
            user = db.first_or_404(db.select(User).filter_by(user_id=user_id))
        except Error as e:
            logging.exception(f"server.py: Error while getting user {user_id}")
        db.session.delete(user)
        db.session.commit()
    return "success"


####################### WEATHER ######################
def new_weather_data(weather_df: pd.DataFrame, city: str, run=0):
    logging.info(f"server.py: saving new weather data for {city} ,run{run} to db ")
    with app.app_context():
        weather_df.to_sql(
            name=city + str(run),
            con=db.engine,
            if_exists='append',
        )
        # db.session.add(weather)
        db.session.commit()


def add_weather_data(weather_df: pd.DataFrame, city):
    with app.app_context():
        pass


def get_weather_data(city: str, run=0) -> Exception | Iterator[DataFrame] | DataFrame:

    with app.app_context():
        try:
            # city_name = pd.read_sql_table(name=city_name, con=db.engine)
            weather = pd.read_sql(sql=city+str(run), con=db) #  , parse_dates=['dt'])
        except OperationalError as e:
            logging.exception("server.py: error in get_weather_data", e)
            return Exception(e)
    return weather

####################### END WEATHER ######################


port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
