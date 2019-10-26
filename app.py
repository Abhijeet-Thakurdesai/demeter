import datetime
from flask import Flask, jsonify, request
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


class FoodSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'description', 'date', 'location', 'zipcode')

# Init schema
food_schema = FoodSchema()
foods_schema = FoodSchema(many=True)


@app.route('/food', methods=['POST'])
def createFood():
    name = request.json["name"]
    location = request.json["location"]
    zipcode = request.json["zipcode"]
    food = Food(name=name, location=location, zipcode=zipcode)
    db.session.add(food)
    db.session.commit()
    return food_schema.jsonify(food), 201
 
@app.route('/food/<zipcode>', methods=['GET'])
def get_product(zipcode):
    food = Food.query.get(zipcode)
    return food_schema.jsonify(food)


if __name__ == '__main__':
    app.run(debug=True)
