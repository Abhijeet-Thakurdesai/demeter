import datetime,uuid,jwt
from functools import wraps
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'psssshhhhh!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    location = db.Column(db.String(500))
    zipcode = db.Column(db.BIGINT())
    user_id = db.Column(db.Integer)


class FoodSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'description', 'date', 'location', 'zipcode')


class UserSchema(ma.Schema):
    class Meta:
        fields = ('public_id', 'username', 'admin')


# Init schema
food_schema = FoodSchema()
foods_schema = FoodSchema(many=True)
user_schema = UserSchema()
user_schema = UserSchema(many=True)
db.create_all()

hashed_password_admin = generate_password_hash("admin", method='sha256')

new_user = User(public_id=str(uuid.uuid4()), username="admin", password=hashed_password_admin, admin=True)
db.session.add(new_user)
db.session.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return make_response("Invalid token", 401)

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return make_response("Invalid token", 401)

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user or not current_user.admin:
        return make_response("Unauthorized operation", 401)

    users = db.session.query(User).all()
    users = user_schema.dump(users, many=True)

    return jsonify(users), 200


@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return make_response("Not Found", 404)

    return user_schema.jsonify([user]), 200


@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return make_response("Unauthorized operation", 401)

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    user = User(public_id=str(uuid.uuid4()), username=data['username'], password=hashed_password, admin=False)
    db.session.add(user)
    db.session.commit()

    return user_schema.jsonify([user]), 201


@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return make_response("Unauthorized operation", 401)

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return user_schema.jsonify([user]), 201


@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return make_response("Not Found", 404)

    db.session.delete(user)
    db.session.commit()

    return  make_response("User deleted", 200)


@app.route('/login', methods=['POST'])
def login():
    username = request.json["username"]
    password = request.json["password"]

    if not username or not password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(username=username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})


@app.route('/food', methods=['POST'])
@token_required
def createFood(current_user):
    name = request.json["name"]
    location = request.json["location"]
    zipcode = request.json["zipcode"]
    food = Food(name=name, location=location, zipcode=zipcode, user_id=current_user.public_id)
    db.session.add(food)
    db.session.commit()
    return food_schema.jsonify(food), 201


@app.route('/food/<zipcode>', methods=['GET'])
@token_required
def get_product(current_user, zipcode):
    food = db.session.query(Food).filter(Food.zipcode == zipcode).all()
    food = food_schema.dump(food, many=True)
    return jsonify(food), 200


if __name__ == '__main__':
    app.run(debug=True)
