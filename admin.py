from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import User, Investment, Notification, Package, WithdrawRequest, Setting, SupportMessage

admin_bp = Blueprint('admin', __name__)

# Middleware to check if user is admin
def admin_required(fn):
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"msg": "Admins only!"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# --- Packaging Routes ---
@admin_bp.route('/packages', methods=['GET'])
@jwt_required()
@admin_required
def get_packages():
    packages = Package.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "amount": p.amount,
        "created_at": p.created_at.isoformat()
    } for p in packages]), 200

@admin_bp.route('/packages', methods=['POST'])
@jwt_required()
@admin_required
def create_package():
    data = request.get_json()
    name = data.get('name')
    amount = data.get('amount')
    
    if not name or not amount:
        return jsonify({"msg": "Missing name or amount"}), 400
        
    package = Package(name=name, amount=amount)
    db.session.add(package)
    db.session.commit()
    return jsonify({"msg": "Package created", "id": package.id}), 201

@admin_bp.route('/packages/<int:package_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_package(package_id):
    package = Package.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    return jsonify({"msg": "Package deleted"}), 200

# --- Withdrawal Routes ---
@admin_bp.route('/withdrawals/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_withdrawals():
    pending = WithdrawRequest.query.filter_by(status='pending').order_by(WithdrawRequest.created_at.asc()).all()
    result = []
    for req in pending:
        user = User.query.get(req.user_id)
        result.append({
            "id": req.id,
            "username": user.username,
            "amount": req.amount,
            "created_at": req.created_at.isoformat()
        })
    return jsonify(result), 200

@admin_bp.route('/withdrawals/approve/<int:req_id>', methods=['POST'])
@jwt_required()
@admin_required
def approve_withdrawal(req_id):
    req = WithdrawRequest.query.get_or_404(req_id)
    if req.status != 'pending':
        return jsonify({"msg": "Request already processed"}), 400
        
    req.status = 'confirmed'
    
    # Deduct from user balance
    user = User.query.get(req.user_id)
    if user.usd_balance < req.amount:
        return jsonify({"msg": "Insufficient user balance"}), 400
        
    user.usd_balance -= req.amount
    
    notification = Notification(
        user_id=user.id,
        message=f"✅ Your withdrawal request of ${req.amount} has been approved.",
        type='success'
    )
    db.session.add(notification)
    db.session.commit()
    return jsonify({"msg": "Withdrawal approved"}), 200

# --- Settings Routes ---
@admin_bp.route('/settings', methods=['GET'])
@jwt_required()
@admin_required
def get_settings():
    settings = Setting.query.all()
    return jsonify({s.key: s.value for s in settings}), 200

@admin_bp.route('/settings', methods=['POST'])
@jwt_required()
@admin_required
def update_settings():
    data = request.get_json()
    for key, value in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            db.session.add(Setting(key=key, value=str(value)))
    db.session.commit()
    return jsonify({"msg": "Settings updated"}), 200

#push go
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "btc_balance": u.btc_balance,
        "usd_balance": u.usd_balance,
        "total_profit": u.total_profit,
        "active_investment": u.active_investment,
        "wallet_address": u.wallet_address,
        "created_at": u.created_at.isoformat()
    } for u in users]), 200

@admin_bp.route('/users/update-stats/<int:user_id>', methods=['POST'])
@jwt_required()
@admin_required
def update_user_stats(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if data.get('usd_balance') is not None: user.usd_balance = float(data.get('usd_balance'))
        if data.get('total_profit') is not None: user.total_profit = float(data.get('total_profit'))
        if data.get('active_investment') is not None: user.active_investment = float(data.get('active_investment'))
        if data.get('btc_balance') is not None: user.btc_balance = float(data.get('btc_balance'))
        if 'wallet_address' in data: user.wallet_address = data['wallet_address']
        
        db.session.commit()
        return jsonify({"msg": "User stats updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to update user: {str(e)}"}), 500

@admin_bp.route('/users/add-investment', methods=['POST'])
@jwt_required()
@admin_required
def add_investment():
    data = request.get_json()
    user_id = data.get('user_id')
    amount_usd = data.get('amount_usd')
    
    if not user_id or not amount_usd:
        return jsonify({"msg": "Missing user_id or amount_usd"}), 400
        
    user = User.query.get_or_404(user_id)
    
    new_inv = Investment(
        user_id=user.id,
        amount_usd=float(amount_usd),
        amount_btc=0.0,
        status='confirmed'
    )
    db.session.add(new_inv)
    
    # Update user balance
    user.usd_balance += float(amount_usd)
    user.active_investment += float(amount_usd)
    
    notification = Notification(
        user_id=user.id,
        message=f"✅ Admin has manually added an investment of ${float(amount_usd):,.2f} to your account.",
        type='success'
    )
    db.session.add(notification)
    
    db.session.commit()
    return jsonify({"msg": "Investment added successfully", "id": new_inv.id}), 201

# --- Investment Routes (Existing) ---
@admin_bp.route('/investments/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_investments():
    pending = Investment.query.filter_by(status='pending').order_by(Investment.created_at.asc()).all()
    
    result = []
    for inv in pending:
        user = User.query.get(inv.user_id)
        result.append({
            "id": inv.id,
            "username": user.username,
            "amount_usd": inv.amount_usd,
            "amount_btc": inv.amount_btc,
            "created_at": inv.created_at.isoformat()
        })
    
    return jsonify(result), 200

@admin_bp.route('/investments/confirm/<int:inv_id>', methods=['POST'])
@jwt_required()
@admin_required
def confirm_investment(inv_id):
    inv = Investment.query.get_or_404(inv_id)
    if inv.status != 'pending':
        return jsonify({"msg": "Investment is already processed"}), 400
        
    inv.status = 'confirmed'
    
    # Update user balance
    user = User.query.get(inv.user_id)
    user.usd_balance += inv.amount_usd
    user.active_investment += inv.amount_usd
    
    # Add notification for the user
    notification = Notification(
        user_id=user.id,
        message=f"✅ Your investment of ${inv.amount_usd:,.2f} has been confirmed!",
        type='success'
    )
    db.session.add(notification)
    
    db.session.commit()
    return jsonify({"msg": "Investment confirmed and balance updated"}), 200

@admin_bp.route('/investments/cancel/<int:inv_id>', methods=['POST'])
@jwt_required()
@admin_required
def cancel_investment(inv_id):
    inv = Investment.query.get_or_404(inv_id)
    if inv.status != 'pending':
        return jsonify({"msg": "Investment is already processed"}), 400
        
    inv.status = 'cancelled'
    
    # Add notification for the user
    notification = Notification(
        user_id=inv.user_id,
        message=f"Your investment request of ${inv.amount_usd:,.2f} was not processed. Please contact support.",
        type='warning'
    )
    db.session.add(notification)
    
    db.session.commit()
    return jsonify({"msg": "Investment cancelled"}), 200

# --- Support Routes ---
@admin_bp.route('/support/conversations', methods=['GET'])
@jwt_required()
@admin_required
def get_support_conversations():
    # Get unique users who have support messages
    user_ids = db.session.query(SupportMessage.user_id).distinct().all()
    conversations = []
    for (uid,) in user_ids:
        user = User.query.get(uid)
        last_msg = SupportMessage.query.filter_by(user_id=uid).order_by(SupportMessage.created_at.desc()).first()
        unread_count = SupportMessage.query.filter_by(user_id=uid, sender='user').count()
        conversations.append({
            "user_id": uid,
            "username": user.username,
            "last_message": last_msg.message if last_msg else "",
            "last_sender": last_msg.sender if last_msg else "",
            "last_time": last_msg.created_at.isoformat() if last_msg else "",
            "unread_count": unread_count
        })
    return jsonify(conversations), 200

@admin_bp.route('/support/messages/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_support_messages(user_id):
    messages = SupportMessage.query.filter_by(user_id=user_id).order_by(SupportMessage.created_at.asc()).all()
    return jsonify([{
        "id": m.id,
        "message": m.message,
        "sender": m.sender,
        "created_at": m.created_at.isoformat()
    } for m in messages]), 200

@admin_bp.route('/support/reply/<int:user_id>', methods=['POST'])
@jwt_required()
@admin_required
def reply_to_user(user_id):
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"msg": "Message cannot be empty"}), 400
    
    new_msg = SupportMessage(
        user_id=user_id,
        message=message,
        sender='admin'
    )
    db.session.add(new_msg)
    db.session.commit()
    
    return jsonify({
        "msg": "Reply sent",
        "id": new_msg.id,
        "message": new_msg.message,
        "sender": new_msg.sender,
        "created_at": new_msg.created_at.isoformat()
    }), 201
