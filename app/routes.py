from .models import User, Product, Order
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt

from flask import request, jsonify, Blueprint

bp = Blueprint('main', __name__)

@bp.route('signup', methods=['POST'])
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username = data['username'],
        email = data['email'],
        role = data['role'],
        password = hashed_password
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully.", "role": new_user.role}), 201

@bp.route('login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username= username).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

# @bp.route("/logout", methods=["DELETE"])
# @jwt_required()
# def logout():
#     jti = get_jwt()["jti"]
#     jwt_redis_blocklist.set(jti, "", ex=ACCESS_EXPIRES)
#     return jsonify(msg="Access token revoked")

@bp.route('product', methods=['POST'])
@jwt_required()
def create_product():
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user and user.role == 'seller':
        data = request.get_json()
        new_product = Product(
            name=data['name'],
            desc=data['desc'],
            price=data['price'],
            user_id =user_id
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Product created successfully"}), 201
    else:
        return jsonify({"msg": "Unauthorized. Only sellers can create products."}), 403

@bp.route('get_all_product', methods=['GET'])
@jwt_required()
def all_products():
    products = Product.query.all()
    all_products = [product.to_dict() for product in products]
    return jsonify(all_products), 200

@bp.route('get_product/<int:id>', methods=['GET'])
@jwt_required()
def product(id):
    product = Product.query.get(id)
    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"msg": "Product not found"}), 404
    
@bp.route('update_product/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    user_id = get_jwt_identity()
    product = Product.query.get(id)

    if product and product.user_id == user_id:
        data= request.get_json()

        product.name = data.get('name', product.name)
        product.desc = data.get('desc', product.desc)
        product.price = data.get('price', product.price)
        db.session.commit()
        return jsonify({'message': 'Product updated successfully'}), 200
    else:
        return jsonify({'error': 'Product not found or you do not have permission to update it'}), 403

@bp.route('delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    user_id = get_jwt_identity()
    product=Product.query.get(id)
    if product and product.user_id == user_id:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    else:
        return jsonify({'error': 'Product not found or you do not have permission to update it'}), 403

@bp.route('orders', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role == 'buyer':
        data = request.get_json()
        order = Order(
            product_id = data['product_id'],
            quantity = data['quantity'],
            customer_name = user.username
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"msg": "Order placed successfully"}), 201
    else:
        return jsonify({"msg": "Unauthorized: Only buyers can place orders"}), 403