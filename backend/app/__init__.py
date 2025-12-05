import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Register blueprints
    from app.routes.papers import papers_bp
    from app.routes.scraper import scraper_bp
    
    app.register_blueprint(papers_bp, url_prefix='/api')
    app.register_blueprint(scraper_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'pyq-finder-api'}
    
    return app
