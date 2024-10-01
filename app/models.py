from app import db

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'price': self.price
        }
