from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Investment, Notification, WithdrawRequest, Setting, Package

investments_bp = Blueprint('investments', __name__)

@investments_bp.route('/request', methods=['POST'])
@jwt_required()
def request_investment():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    amount_usd = data.get('amount_usd')
    
    if not amount_usd:
        return jsonify({"msg": "Missing amount"}), 400
        
    new_investment = Investment(
        user_id=user_id,
        amount_usd=amount_usd,
        amount_btc=0.0,
        status='pending'
    )
    
    db.session.add(new_investment)
    
    # Add notification for the user
    notification = Notification(
        user_id=user_id,
        message=f"Investment request for ${amount_usd:,.2f} submitted. Pending confirmation.",
        type='info'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({"msg": "Investment request submitted", "id": new_investment.id}), 201

@investments_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_investments():
    user_id = get_jwt_identity()
    investments = Investment.query.filter_by(user_id=user_id).order_by(Investment.created_at.desc()).all()
    
    return jsonify([{
        "id": inv.id,
        "amount_usd": inv.amount_usd,
        "amount_btc": inv.amount_btc,
        "status": inv.status,
        "created_at": inv.created_at.isoformat()
    } for inv in investments]), 200

@investments_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def request_withdrawal():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({"msg": "Missing amount"}), 400
        
    user = User.query.get(user_id)
    if user.usd_balance < amount:
        return jsonify({"msg": "Insufficient balance"}), 400
        
    new_request = WithdrawRequest(user_id=user_id, amount=amount)
    db.session.add(new_request)
    
    notification = Notification(
        user_id=user_id,
        message=f"Withdrawal request of ${amount} submitted. Pending admin approval.",
        type='info'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({"msg": "Withdrawal request submitted", "id": new_request.id}), 201

@investments_bp.route('/packages', methods=['GET'])
@jwt_required()
def get_packages():
    packages = Package.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "amount": p.amount,
        "created_at": p.created_at.isoformat()
    } for p in packages]), 200

@investments_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_public_settings():
    # Only expose specific settings to users
    wallet = Setting.query.filter_by(key='wallet_address').first()
    website = Setting.query.filter_by(key='website_url').first()
    
    return jsonify({
        "wallet_address": wallet.value if wallet else "",
        "website_url": website.value if website else ""
    }), 200
