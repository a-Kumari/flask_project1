from .models import User, Product, Order, CartItem, Address, Category, SubCategory, Discount, Receipt
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import datetime
from flask import request, jsonify, Blueprint
from .pdf_utils import generate_receipt_pdf, send_invoice_email_with_pdf
import uuid
import os

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
        return jsonify(access_token=access_token, role= user.role), 200
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
            seller_id=user_id,
            subcategory_id = data['subcategory_id'],
            tags = data['tags']
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Product created successfully", 
            'product_id': new_product.id,
            'name': new_product.name,
            'description': new_product.desc,
            'price': new_product.price,
            'category_id': new_product.subcategory_id,
            'tags': new_product.tags,
            'stock': new_product.stock}), 201
    else:
        return jsonify({"msg": "Unauthorized. Only sellers can create products."}), 403


# This api to get all the product
@bp.route('get_all_product', methods=['GET'])
@jwt_required()
def all_products():
    products = Product.query.all()
    current_date = datetime.datetime.now()
    all_products = []

    for product in products:
        subcategory = SubCategory.query.filter_by(id=product.subcategory_id).first()
        category_id = subcategory.category_id if subcategory else None

        # here it get the discount for product category 
        discount = Discount.query.filter(
            Discount.category_id == category_id,
            Discount.is_active == True
        ).first()
        # here if the discount exists and the end date has expired it deactive 
        if discount and discount.end_date < current_date:
            discount.is_active = False
            db.session.commit()
            discount = None  

        # Calculate discount price if applicable
        if discount:
            discount_amount = product.price * (discount.discount / 100)
            discount_price = product.price - discount_amount
        else:
            discount_price = product.price
        product_data = {
            'product_id': product.id,
            'name': product.name,
            'description': product.desc,
            'original_price': product.price,
            'discounted_price': discount_price,
            'discount': discount.discount if discount else 0,
            'category_id': category_id,
            'tags': product.tags,
            'stock': product.stock
        }
        
        all_products.append(product_data)

    
    return jsonify(all_products), 200


# This api to get a particular product
@bp.route('get_product/<int:id>', methods=['GET'])
@jwt_required()
def product(id):
    product = Product.query.get(id)
    current_date = datetime.datetime.now()

    if product:
        subcategory = SubCategory.query.filter_by(id=product.subcategory_id).first()
        category_id = subcategory.category_id if subcategory else None

        discount = Discount.query.filter(
        Discount.category_id == category_id,
        Discount.is_active == True
        ).first()
        # here if the discount exists and the end date has expired it deactive 
        if discount and discount.end_date < current_date:
            discount.is_active = False
            db.session.commit()
            discount = None  

        # Calculating the discount price if avaliable
        if discount:
            discount_amount = product.price * (discount.discount / 100)
            discount_price = product.price - discount_amount
        else:
            discount_price = product.price
        product_data = {
            'product_id': product.id,
            'name': product.name,
            'description': product.desc,
            'original_price': product.price,
            'discounted_price': discount_price,
            'discount': discount.discount if discount else 0,
            'category_id': category_id,
            'tags': product.tags,
            'stock': product.stock
            }

        return jsonify(product_data), 200
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
        product.stock = data.get('stock', product.stock)
        product.tags = data.get('tags', product.tags)
        db.session.commit()
        product_data = {
            'product_id': product.id,
            'name': product.name,
            'description': product.desc,
            'original_price': product.price,
            'category_id': product.sub_category_id,
            'tags': product.tags,
            'stock': product.stock
        }
        return jsonify({'message': 'Product updated successfully'}, product_data), 200
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
        return jsonify({'error': 'Product not found or you do not have permission to delete it'}), 403

# This api is for placing order
@bp.route('place_order', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    address_id = data.get('address_id')
    if user.role == 'buyer':
        cart_items = CartItem.query.filter_by(buyer_id =user_id).all() # here query is done on CartItem table to get all the items from the particular user cart.
        if not cart_items:
            return jsonify({"message": "Your cart is empty. Cannot place an order."}), 400
        
        address = Address.query.filter_by(id=address_id, buyer_id=user_id).first() # here query is done on Address table in which I am comparing the address_id and buyer_id with the address_id which is provided in request and user who loged.

        if not address:
            return jsonify({"error": "Address not found or does not belong to the buyer"}), 403

        orders = []
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)

            if product.stock < cart_item.quantity: # here it is checked wheather the given product quantity is greater than the product stock and if it is the api will stop and show the given error massage.
                return jsonify({
                    "error": f"Insufficient stock for product ID {product.id}. Cannot place the order."
                }), 400
            current_date = datetime.datetime.now()
            subcategory = SubCategory.query.filter_by(id=product.subcategory_id).first()
            category_id = subcategory.category_id if subcategory else None

            discount = Discount.query.filter(
                Discount.category_id == category_id,
                Discount.is_active == True,
                Discount.start_date <= current_date,
                Discount.end_date >= current_date
            ).first()
            if discount:
                discount_amount = (product.price * cart_item.quantity) * (discount.discount / 100)
                total_price = (product.price * cart_item.quantity) - discount_amount
            else:
                total_price = product.price * cart_item.quantity

            product.stock -= cart_item.quantity # here one item quantity is deducted from the product stock.
            order = Order(
                product_id = cart_item.product_id,
                quantity = cart_item.quantity,
                total_price=total_price,
                price = product.price,
                buyer_id = user.id,
                address_id = address_id
            )
            db.session.add(order)
            orders.append(order)
            total_final_amount += total_price

        CartItem.query.filter_by(buyer_id=user_id).delete() # after adding the order in order table it is removing all the items from the cart of the user.
        db.session.commit()

        receipt_id = str(uuid.uuid4())
        order_data = [{
            "product_id": order.product_id,
            "quantity": order.quantity,
            "price": order.price,
            "total_price": order.total_price,
            "discount_applied": discount.discount if discount else 0
        } for order in orders]

        pdf_path= generate_receipt_pdf(order_data, user_id, receipt_id)
        send_invoice_email_with_pdf(user.email, receipt_id, pdf_path)
        new_receipt = Receipt(
            receipt_id=receipt_id,
            user_id=user_id,
            order_id=order.id
        )
        db.session.add(new_receipt)
        db.session.commit()


        return jsonify({"msg": "Order placed successfully", "orders": [{
            "order_id": order.id, 
            "product_id": order.product_id,
            "quantity": order.quantity,
            "buyer_id": order.buyer_id,
            "price": order.price,
            "total_price": order.total_price,
            "discount_applied": discount.discount if discount else 0,
            "placed_at": order.placed_at.strftime("%Y-%m-%d %H:%M:%S"),
            "address_id": order.address_id
            } for order in orders
            ],
            "total_final_amount": total_final_amount,

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
                    'price': order.price,
                    "total_price": order.total_price
                })
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
        "quantity": cart_item.quantity,
        "price" : product.price
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
        product = Product.query.filter_by(id=item.product_id).first()

        subcategory = SubCategory.query.filter_by(id=product.subcategory_id).first()
        category_id = subcategory.category_id if subcategory else None
        current_date = datetime.datetime.now()
        discount = Discount.query.filter(
            Discount.category_id == category_id,
            Discount.is_active == True,
            Discount.start_date <= current_date,
            Discount.end_date >= current_date
        ).first()
        if discount:
            discount_amount = (product.price * item.quantity) * (discount.discount / 100)
            total_price = (product.price * item.quantity) - discount_amount
        else:
            total_price = product.price * item.quantity

        cart_items.append({
            'product_id': item.product_id,
            'quantity': item.quantity,
            'buyer_id': item.buyer_id,
            'price': product.price,
            'total_price': total_price
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
    address_id = data.get('address_id')

    product= Product.query.filter_by(id= product_id).first() # here query is done on Product table where id is compared with the provided product_id in url.
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.stock < quantity:
        return jsonify({"error": "Insufficient stock available"}), 400
    
    
    address = Address.query.filter_by(id=address_id, buyer_id=user_id).first() # here query is done on Address table in which I am comparing the address_id and buyer_id with the address_id which is provided in request and user who loged.
    if not address:
        return jsonify({"error": "Address not found or does not belong to the buyer"}), 403

    current_date= datetime.datetime.now()
    subcategory = SubCategory.query.filter_by(id=product.subcategory_id).first()
    category_id = subcategory.category_id if subcategory else None

    discount = Discount.query.filter(
        Discount.category_id == category_id,
        Discount.is_active == True,
        Discount.start_date <= current_date,
        Discount.end_date >= current_date).first()
    if discount:
        discount_amount = (product.price * quantity) * (discount.discount/100)
        total_price = (product.price * quantity) - discount_amount
    else:
        total_price = product.price * quantity
    new_order = Order(
        buyer_id=user_id,
        product_id=product_id,
        quantity=quantity,
        price = product.price,
        total_price=total_price,
        address_id =address_id
    )
    db.session.add(new_order)
    product.stock -= quantity
    db.session.commit()
    receipt_id = str(uuid.uuid4())
    orders = {
            "product_id": new_order.product_id,
            "quantity": new_order.quantity,
            "price": new_order.price,
            "total_price": new_order.total_price,
            "discount_applied": discount.discount if discount else 0
        } 
    pdf_path = generate_receipt_pdf(orders, user_id, receipt_id)
    send_invoice_email_with_pdf(user.email, receipt_id, pdf_path)
    new_receipt = Receipt(
        receipt_id=receipt_id,
        user_id=user_id,
        order_id=new_order.id
    )
    db.session.add(new_receipt)
    db.session.commit()  

    return jsonify({
        'message': 'Order placed successfully',
        'order_id': new_order.id,
        'product_id': product_id,
        'quantity': quantity,
        'price': new_order.price,
        'total_price': new_order.total_price,
        'discount': discount.discount if discount else 0,
        'address':new_order.address_id
    }), 201

# this api to create address 
@bp.route('create_address', methods=['POST'])
@jwt_required()
def create_address():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role !='buyer':
        return jsonify({"message": "Access denied: Sellers cannot create address."}), 403
    data = request.get_json()
    country = data.get('country')
    address_line1 = data.get('address_line1')
    address_line2 = data.get('address_line2')
    landmark = data.get('landmark')
    pincode = data.get('pincode')
    city = data.get('city')
    state = data.get('state')
    is_default = data.get('is_default')
    if not country or not address_line1 or not pincode or not city or not state:
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_address = Address(
        buyer_id=user_id,
        country=country,
        address_line1 = address_line1,
        address_line2 = address_line2,
        landmark=landmark,
        pincode=pincode,
        city=city,
        state=state,
        is_default=is_default
    )
    db.session.add(new_address)
    db.session.commit()
    
    return jsonify({'message': 'Address created successfully',
        'buyer_id': new_address.buyer_id,
        'country': new_address.country,
        'address_line1':new_address.address_line1,
        'address_line2': new_address.address_line2,
        'landmark': new_address.landmark,
        'pincode': new_address.pincode,
        'city': new_address.city,
        'state': new_address.state,
    }), 201

# this api is to update address of the buyer where the product will be delivered
@bp.route('update_address/<int:address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    user_id = get_jwt_identity()
    address = Address.query.get(address_id)

    if address and address.buyer_id == user_id:
        data= request.get_json()

        address.country = data.get('country', address.country)
        address.address_line1 = data.get('address_line1', address.address_line1)
        address.address_line2 = data.get('address_line2', address.address_line2)
        address.landmark = data.get('landmark', address.landmark)
        address.pincode = data.get('pincode', address.pincode)
        address.city = data.get('city', address.city)
        address.state = data.get('state', address.state)
        address.is_default = data.get('is_default', address.is_default)
        db.session.commit()
        return jsonify({'message': 'Address updated successfully',
                        'country': address.country,
                        'address_line1': address.address_line1,
                        'address_line2': address.address_line2,
                        'landmark': address.landmark,
                        'pincode':address.pincode,
                        'city': address.city,
                        'state': address.state,
                        'is_default':address.is_default}), 200
    else:
        return jsonify({'error': 'Address not found or you do not have permission to update it'}), 403

# this api is to delete the address
@bp.route('delete_address/<int:address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    user_id = get_jwt_identity()
    address=Address.query.get(address_id)
    if address and address.buyer_id == user_id:
        db.session.delete(address)
        db.session.commit()
        return jsonify({'message': 'Address deleted successfully'}), 200
    else:
        return jsonify({'error': 'Address not found or you do not have permission to delete it'}), 403

# this api is to create categories 
@bp.route('category', methods=['POST'])
@jwt_required()
def create_category():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role not in ['seller', 'admin']:
        return jsonify({"message": "Access denied: only sellers or admins can create a category."}), 403
        
    data = request.get_json()
    new_category =Category(
        name = data['name']
    )
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'message': 'Address created successfully', 
                    'name': new_category.name}), 200

# this api is to create sub_category
@bp.route('sub_category', methods=['POST'])
@jwt_required()
def create_sub_category():
    user_id =get_jwt_identity()
    user=User.query.get(user_id)
    if user.role not in ['seller', 'admin']:    # here it check if the loged in user is either asell or admin if not it will show error message.
        return jsonify({"message": "Access denied: only sellers or admins can create a sub_category."}), 403
        
    data = request.get_json()
    new_subcategory =SubCategory(
        name = data['name'],
        category_id =data['category_id']
    )
    db.session.add(new_subcategory)
    db.session.commit()
    return jsonify({'message': 'Address created successfully', 
                    'name': new_subcategory.name,
                    'category_id':new_subcategory.category_id}), 200

# this api is to create discount on a category
@bp.route('discount/<int:category_id>', methods=['POST'])
@jwt_required()
def create_discount(category_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role != 'admin':
        return jsonify({"message": "Access denied: Only admin is allowed."}), 403
    
    data = request.get_json()

    existing_discount = Discount.query.filter_by(category_id=category_id, is_active=True).first()
    if existing_discount:
        if existing_discount.start_date <= datetime.datetime.now() <= existing_discount.end_date: # here it check it the current date and time is between the start_date and end_date if it is it will show error message and new discount cannot be created
            return jsonify({"message": "An active discount already exists for this category."})
        else:
            existing_discount.is_active = False  # here if the current datetime is above the end_date and is_active is true than it will convert the is_active to flase.
            db.session.commit()

    new_discount = Discount(
        category_id = category_id,
        discount = data['discount'],
        is_active = data['is_active'],
        end_date = data['end_date']
    )
    db.session.add(new_discount)
    db.session.commit()
    return jsonify({'msg': 'Discount created sucessfully',
                    'category_id': new_discount.category_id, 
                    'discount': new_discount.discount, 
                    'is_active': new_discount.is_active,
                    'start_date': new_discount.start_date,
                    'end_date': new_discount.end_date,
                    }), 200

@bp.route('buyer_order', methods=['GET'])
@jwt_required()
def buyer_order():
    user_id = get_jwt_identity()
    user= User.query.get(user_id)
    if user.role != 'buyer':
        return jsonify({"message": "Access denied: Only buyer is allowed."}), 403
    orders = Order.query.filter_by(buyer_id = user_id)

    order_list = [{
            'id': order.id,
            'product_id': order.product_id,
            'quantity': order.quantity,
            'total_price': order.total_price,
            'price': order.price,
            'order_date': order.placed_at,
            'address': order.address_id
        } for order in orders]
    return jsonify({'orders': order_list}), 200

