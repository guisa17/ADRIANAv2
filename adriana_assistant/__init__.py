import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] = 'df29d08d8594f0bc3719a48ba4132db5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'adriana.bot314@gmail.com'
app.config['MAIL_PASSWORD'] = 'adrianabot123'
# app.config['MAIL_DEFAULT_SENDER'] = 'adriana.bot314@gmail.com'
mail = Mail(app)

from adriana_assistant import routes
from adriana_assistant.chatbot import chatbot_bp

app.register_blueprint(chatbot_bp)
