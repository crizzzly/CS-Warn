import os
import requests
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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


with app.app_context():
    db.create_all()


@app.route('/')
def index(word):
    return redirect(url_for(user_list))


@app.route("/users")
def user_list():
    users = db.session.execute(db.select(User).order_by(User.name)).scalars()
    return users


@app.route("/new", methods=["GET", "POST"])
def user_add(name="None", telegram_uid="None", lat=0, lon=0):
    user = User(
        name=name,
        id=telegram_uid,
        lat=lat,
        lon=lon,
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()
    return "success??"


@app.route("/user/<int:id>")
def user_detail(id):
    user = db.get_or_404(User, id)
    return user


@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
def user_delete(id):
    user = db.get_or_404(User, id)

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        return "success"

    return "success"


port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=port)
