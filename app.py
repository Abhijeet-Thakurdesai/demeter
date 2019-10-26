import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    location = db.Column(db.String(500))
    zipcode = db.Column(db.BIGINT())

class FoodSchema(ma.ModelSchema):
    class Meta:
        model = Food

db.create_all()
if __name__ == '__main__':
    app.run(debug=True)