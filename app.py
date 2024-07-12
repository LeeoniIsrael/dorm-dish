from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_bcrypt import Bcrypt
from sqlalchemy.dialects.postgresql import JSON
from openai import OpenAI
import os
from dotenv import load_dotenv
import pprint

load_dotenv()

GPT_API_KEY = os.getenv('GPT_API_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users-dorm.db'
app.permanent_session_lifetime = timedelta(days = 5)
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

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/recipe')
def recipe():
    return render_template('recipe.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']

        print(f"Signup POST data: email={email}, password={password}, confirm_password={confirm_password}")

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        print(f"Login POST data: email={email}, password={password}")
        print(f"User found: {user}")

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user"] = user.email
            session["logged_in"] = True
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if session.get("logged_in"):
        email = session.get("user")
        user = User.query.filter_by(email=email).first()
        return f'Hello, {user.email}!'
    else:
        flash('You need to login first.', 'warning')
        return redirect(url_for("login"))
    
def parse_recipes(text):
    recipes = {}
    recipe_blocks = text.split("\n\n")
    for i, block in enumerate(recipe_blocks, start=1):
        lines = block.split("\n")
        name = lines[0].replace("Recipe Name:", "").strip()
        ingredients = []
        in_ingredients = False
        for line in lines[1:]:
            if line.startswith("Ingredients:"):
                in_ingredients = True
            elif in_ingredients:
                if line.startswith("- "):
                    ingredients.append(line[2:])
        recipes[i] = {
            "name": name,
            "ingredients": ingredients
        }
    return recipes

@app.route('/get_recipes', methods=['GET', 'POST'])
def get_recipes():
    ingredients = request.form.get('ingredients')
    client = OpenAI(api_key=GPT_API_KEY)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a cooking expert that provides recipes based on any ingredients. Each recipe should be formatted as: Recipe Name: Ingredients: - Ingredient 1 - Ingredient 2 - ..."},
            {"role": "user", "content": f"Here are the ingredients: {ingredients}. What recipes can I make?"}
        ]
    )
    recipes_text = completion.choices[0].message.content
    recipes = parse_recipes(recipes_text)
    session['recipes'] = recipes 
    return jsonify({'recipes': recipes})

@app.route('/fetch_recipes', methods=['GET'])
def fetch_recipes():
    recipes = session.get('recipes')
    return jsonify({'recipes': recipes})

@app.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')


@app.route('/users')
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)