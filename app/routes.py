from .models import User, Product, Order, CartItem
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from datetime import datetime
from flask import request, jsonify, Blueprint

bp = Blueprint('main', __name__)

# this api is for signup
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

# This api is for login
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

# this api to create product, only the seller can create a product
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
            stock=data['stock'],
            seller_id=user_id
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Product created successfully"}), 201
    else:
        return jsonify({"msg": "Unauthorized. Only sellers can create products."}), 403

# This api to get all the product
@bp.route('get_all_product', methods=['GET'])
@jwt_required()
def all_products():
    products = Product.query.all()
    all_products = [product.to_dict() for product in products]
    return jsonify(all_products), 200


# This api to get a particular product
@bp.route('get_product/<int:id>', methods=['GET'])
@jwt_required()
def product(id):
    product = Product.query.get(id)
    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"msg": "Product not found"}), 404
    

# This api for updating the product   
@bp.route('update_product/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    user_id = get_jwt_identity()
    product = Product.query.get(id)

    if product and product.seller_id == user_id:
        data= request.get_json()

        product.name = data.get('name', product.name)
        product.desc = data.get('desc', product.desc)
        product.price = data.get('price', product.price)
        db.session.commit()
        return jsonify({'message': 'Product updated successfully'}), 200
    else:
        return jsonify({'error': 'Product not found or you do not have permission to update it'}), 403

# This api for deleting the product which is only deleted who created that product.
@bp.route('delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    user_id = get_jwt_identity()
    product=Product.query.get(id)
    if product and product.seller_id == user_id:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    else:
        return jsonify({'error': 'Product not found or you do not have permission to update it'}), 403

# This api is for placing order
@bp.route('place_order', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role == 'buyer':
        cart_items = CartItem.query.filter_by(buyer_id =user_id).all() # here query is done on CartItem table to get all the items from the particular user cart.
        if not cart_items:
            return jsonify({"message": "Your cart is empty. Cannot place an order."}), 400
        
        orders = []
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)

            if product.stock < cart_item.quantity: # here it is checked wheather the given product quantity is greater than the product stock and if it is the api will stop and show the given error massage.
                return jsonify({
                    "error": f"Insufficient stock for product ID {product.id}. Cannot place the order."
                }), 400

            product.stock -= cart_item.quantity # here one item quantity is deducted from the product stock.
            order = Order(
                product_id = cart_item.product_id,
                quantity = cart_item.quantity,
                total_price=product.price * cart_item.quantity,
                buyer_id = user.id
            )
            db.session.add(order)
            orders.append(order)
        CartItem.query.filter_by(buyer_id=user_id).delete() # after adding the order in order table it is removing all the items from the cart of the user.
        db.session.commit()
        return jsonify({"msg": "Order placed successfully", "orders": [{
            "order_id": order.id, 
            "product_id": order.product_id,
            "quantity": order.quantity,
            "buyer_id": order.buyer_id,
            "total_price": order.total_price
            } for order in orders
            ]
        }), 201
    else:
        return jsonify({"msg": "Unauthorized: Only buyers can place orders"}), 403

# # This api is to get list of order for seller product
@bp.route('get_order', methods=['GET'])
@jwt_required()
def get_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role == 'seller':

        products = Product.query.filter_by(seller_id = user_id).all()
        if not products:
            return jsonify({"message": "No products found for this seller"}), 404
        all_orders = []
        for product in products:
            orders = Order.query.filter_by(product_id=product.id).all()
            for order in orders:
                all_orders.append({"order_id": order.id,
                    "product_id": order.product_id,
                    "buyer_id": order.buyer_id,
                    "quantity": order.quantity,
                    "total_price": order.total_price,
                    "placed_at": order.placed_at.strftime("%Y-%m-%d %H:%M:%S") })
        return jsonify(all_orders)
    else:
        return jsonify({"message": "Access denied: Buyers cannot view order list."}), 403

# This api to add product to cart in which I am providing the product id in url only
@bp.route('add_to_cart/<int:product_id>', methods=['POST'])
@jwt_required()
def add_to_cart(product_id):
    user_id = get_jwt_identity() # here I am getting the user_id which I have given as identity while creating access token
    data = request.get_json()
    quantity = data.get('quantity')

    if not product_id or quantity <= 0: 
        return jsonify({"message": "Invalid data"}), 400
    
    product = Product.query.get(product_id)
    if product.stock < quantity:
        return jsonify({"error": "Insufficient stock available"}), 400

    cart_item = CartItem.query.filter_by(buyer_id = user_id, product_id= product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item= CartItem(buyer_id = user_id, product_id= product_id, quantity= quantity)
        db.session.add(cart_item)
    db.session.commit()
    return jsonify({
    "message": "Item added to cart",
    "cart_item": {
        "id": cart_item.id,
        "product_id": cart_item.product_id,
        "buyer_id": cart_item.buyer_id,
        "quantity": cart_item.quantity
        }
    }), 200

# This api is to get the buyer cart items which buyer added to cart
@bp.route('get_item', methods=['GET'])
@jwt_required()
def get_buyer_item():
    user_id= get_jwt_identity()
    user = User.query.get(user_id)
    if user.role != 'buyer':
        return jsonify({"message": "Access denied: Sellers cannot view cart items."}), 403

    buyer_cart_items = CartItem.query.filter_by(buyer_id=user_id).all()
    if not buyer_cart_items:
        return jsonify({"message": "Your cart is empty."}), 200
    
    cart_items = []
    for item in buyer_cart_items:
        cart_items.append({
            'product_id': item.product_id,
            'quantity': item.quantity,
            'buyer_id': item.buyer_id
        })

    return jsonify(cart_items), 200


# this api is to delete cart item from cart
@bp.route('remove_item/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_item(product_id):
    user_id = get_jwt_identity()
    user =User.query.get(user_id)
    if user.role !='buyer':
        return jsonify({"message": "Access denied: Sellers cannot remove cart items."}), 403
    cart_item = CartItem.query.filter_by(buyer_id=user_id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Product not found in cart."}), 200

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        db.session.commit()
        return jsonify({'message': 'Product quantity decreased by 1', 'quantity': cart_item.quantity}), 200
    else: 
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message: Product removed from cart"})


# this api is to buy the product directly without adding it to cart
@bp.route('buy_now/<int:product_id>', methods=['POST'])
@jwt_required()
def buy_now(product_id):
    user_id = get_jwt_identity()
    user =User.query.get(user_id)
    if user.role !='buyer':
        return jsonify({"message": "Access denied: Sellers cannot place order."}), 403

    data = request.get_json()
    quantity= data.get('quantity')

    product= Product.query.filter_by(id= product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.stock < quantity:
        return jsonify({"error": "Insufficient stock available"}), 400

    new_order = Order(
        buyer_id=user_id,
        product_id=product_id,
        quantity=quantity,
        total_price=product.price * quantity
    )
    db.session.add(new_order)
    product.stock -= quantity
    db.session.commit()
    return jsonify({
        'message': 'Order placed successfully',
        'order_id': new_order.id,
        'product_id': product_id,
        'quantity': quantity,
        'total_price': new_order.total_price
    }), 201