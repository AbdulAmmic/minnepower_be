from extensions import db, bcrypt, jwt

from flask import Flask
from flask_cors import CORS
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///minnepower.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your-super-secret-key' # In production, use env variable
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    with app.app_context():
        import models
        db.create_all()
        
        # Create a default admin if it doesn't exist
        admin = models.User.query.filter_by(username='admin').first()
        if not admin:
            hashed_pw = bcrypt.generate_password_hash('1-8').decode('utf-8')
            admin = models.User(
                username='admin',
                email='admin@admin',
                password=hashed_pw,
                role='admin',
                btc_balance=0.0,
                usd_balance=0.0
            )
            db.session.add(admin)
            print("Created default admin user: admin / 1-8")
        
        # Seed default packages
        if not models.Package.query.first():
            packages = [
                models.Package(name='Starter', amount=200.0),
                models.Package(name='Medium', amount=500.0),
                models.Package(name='Gold', amount=1000.0),
                models.Package(name='Silver', amount=5000.0)
            ]
            db.session.bulk_save_objects(packages)
            print("Seeded default packages")

        # Seed default settings
        if not models.Setting.query.filter_by(key='wallet_address').first():
            db.session.add(models.Setting(key='wallet_address', value='Your-BTC-Wallet-Address-Here'))
        if not models.Setting.query.filter_by(key='website_url').first():
            db.session.add(models.Setting(key='website_url', value='https://example.com'))
            
        db.session.commit()

    # Register blueprints (routes)
    from auth import auth_bp
    from investments import investments_bp
    from admin import admin_bp
    from notifications_route import notifications_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(investments_bp, url_prefix='/api/investments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
