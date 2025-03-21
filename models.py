from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    worthiness = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)
    premium = db.Column(db.Boolean, default=False)
    
    # Relationship with Transactions
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "lent" or "borrowed"
    person_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.String(50), default=str(datetime.now().strftime("%x")))
    time_period = db.Column(db.String(50), nullable=False)  # Duration (e.g., "6 months", "2 years")
    rate = db.Column(db.Float, nullable=False)  # Interest rate
    lend_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class LendingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    time_period = db.Column(db.String(50), nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.String(50), default=str(datetime.now().strftime("%x")))
    
    user = db.relationship('User', backref=db.backref('lending_requests', lazy=True))

class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, unique=True, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.String(64), nullable=False)
    transactions = db.relationship('BlockchainTransaction', backref='block', lazy=True, cascade="all, delete-orphan")

class BlockchainTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=False)
    lender = db.Column(db.String(50), nullable=False)
    borrower = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.String(64), nullable=False)