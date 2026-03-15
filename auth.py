from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"msg": "Missing required fields"}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400
        
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter((User.username == username) | (User.email == username)).first()
    if user and bcrypt.check_password_hash(user.password, password):
        # Store user role in token for security
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "btc_balance": user.btc_balance,
                "usd_balance": user.usd_balance,
                "total_profit": user.total_profit,
                "active_investment": user.active_investment
            }
        }), 200
        
    return jsonify({"msg": "Bad username or password"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "btc_balance": user.btc_balance,
        "usd_balance": user.usd_balance,
        "total_profit": user.total_profit,
        "active_investment": user.active_investment
    }), 200
