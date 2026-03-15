from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        "id": n.id,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in notifications]), 200

@notifications_bp.route('/read/<int:note_id>', methods=['POST'])
@jwt_required()
def mark_read(note_id):
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(id=note_id, user_id=user_id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({"msg": "Notification marked as read"}), 200
