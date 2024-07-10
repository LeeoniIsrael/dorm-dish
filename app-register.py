from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.dialects.postgresql import JSON

app = Flask(__name__)
app.config['SECRET_KEY'] = 'averysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users-dorm.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    data = db.Column(JSON, default=list)
    
    def __init__(self, email, password, data=None):
      self.email = email
      self.password = password
      self.data = data if data is not None else []
def create_tables():
  with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "hello world!"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('/'))

# @app.route('/login', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         #query db for email and password.
#         flash('Passwords do not match')
#         return redirect(url_for('signup'))
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

#         new_user = User(email=email, password=hashed_password)
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Your account has been created!', 'success')
#         return redirect(url_for('login'))
#     return render_template('signup.html')



if __name__ == '__main__':
    create_tables()
    app.run(debug=True)