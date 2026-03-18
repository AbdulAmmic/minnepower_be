from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'
    btc_balance = db.Column(db.Float, default=0.0)
    usd_balance = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    active_investment = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    investments = db.relationship('Investment', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_usd = db.Column(db.Float, nullable=False)
    amount_btc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'confirmed', 'cancelled'
    btc_address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), default='info') # 'success', 'info', 'warning'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WithdrawRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'confirmed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_rel = db.relationship('User', backref='withdraw_requests')

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_rel = db.relationship('User', backref='support_messages')
