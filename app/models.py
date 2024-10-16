from app import db
import datetime
from sqlalchemy import JSON


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String, nullable=False)
    email= db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String(10), nullable=False)  


    __table_args__ = (
        db.CheckConstraint("role IN ('buyer', 'seller', 'admin')"),
    )

class Category(db.Model):
    id = db.Column(db.Integer, primary_key = True, index=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class SubCategory(db.Model):
    __tablename__= "subcategory"
    id = db.Column(db.Integer, primary_key = True, index=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __repr__(self):
        return f'<SubCategory {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name= db.Column(db.String, nullable=False)
    desc = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock = db.Column(db.Integer, nullable=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=False)
    tags = db.Column(JSON, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    placed_at = db.Column(db.DateTime, default=datetime.datetime.now)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)


    def __repr__(self):
        return f'<Order {self.buyer_id}>'

class CartItem(db. Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<CartItem {self.id}>'
    
class Address(db.Model):
    id = db.Column(db.Integer, primary_key = True, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    address_line1 = db.Column(db.String(100), nullable=False)
    address_line2= db.Column(db.String(100))
    landmark = db.Column(db.String(100))
    pincode = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Address {self.buyer_id}>'




class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    discount = db.Column(db.Integer, nullable=False)  
    is_active = db.Column(db.Boolean, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.datetime.now)
    end_date = db.Column(db.DateTime, nullable=True)
   
    def __repr__(self):
        return f'<Discount {self.discount}>'

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    receipt_id = db.Column(db.String, nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.datetime.now)
