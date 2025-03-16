from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from models import db
from routes import routes, login_manager, bcrypt

# Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Use PostgreSQL/MySQL in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)
bcrypt.init_app(app)
login_manager.init_app(app)

# Register Routes
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
