from app import db
import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String, nullable=False)
    email= db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String(10), nullable=False)  


    __table_args__ = (
        db.CheckConstraint('role IN ("buyer", "seller")'),
    )
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name= db.Column(db.String, nullable=False)
    desc = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'price': self.price
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id')) # use id of user table instead of customername
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    product = db.relationship('Product', backref='orders')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'buyer_id': self.buyer_id
        }

    def __repr__(self):
        return f'<Order {self.buyer_id}>'

class CartItem(db. Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
