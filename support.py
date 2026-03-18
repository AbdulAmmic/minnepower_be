from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import SupportMessage, User

support_bp = Blueprint('support', __name__)

@support_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    user_id = get_jwt_identity()
    messages = SupportMessage.query.filter_by(user_id=user_id).order_by(SupportMessage.created_at.asc()).all()
    
    return jsonify([{
        "id": m.id,
        "message": m.message,
        "sender": m.sender,
        "created_at": m.created_at.isoformat()
    } for m in messages]), 200

@support_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    user_id = get_jwt_identity()
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"msg": "Message cannot be empty"}), 400
    
    new_msg = SupportMessage(
        user_id=user_id,
        message=message,
        sender='user'
    )
    db.session.add(new_msg)
    db.session.commit()
    
    return jsonify({
        "msg": "Message sent",
        "id": new_msg.id,
        "message": new_msg.message,
        "sender": new_msg.sender,
        "created_at": new_msg.created_at.isoformat()
    }), 201
