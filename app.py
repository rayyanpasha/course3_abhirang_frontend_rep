from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE = 'AbhiRang.db' # Replace with your actual database path if necessary

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Helper functions
def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM user WHERE email = '{email}'")  # Using f-string here (not recommended for user data directly)
    user = cursor.fetchone()
    conn.close()
    return user

# User Registration
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    required_fields = ['username', 'email', 'password', 'phone_number', 'user_type']
    
    # Validate all required fields are present
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    # Check if the user already exists
    if get_user_by_email(data['email']):
        return jsonify({"error": "User already exists"}), 400

    # Hash the password
    password_hash = generate_password_hash(data['password'])
    is_verified = 1 if data['user_type'] == 'artist' else 0

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'''
            INSERT INTO "user" (username, password_hash, email, phone_number, user_type, is_verified)
            VALUES ('{data['username']}', '{password_hash}', '{data['email']}', '{data['phone_number']}', '{data['user_type']}', {is_verified})
        ''')  # Using f-string to insert values (again, not ideal for user input directly)
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    conn.close()
    return jsonify({"message": "Registration successful!"}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    
    # Validate email and password presence
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user_by_email(data['email'])
    
    # Check if user exists and password is correct
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful!"}), 200

# Categories Retrieval
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM category')
    categories = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in categories])

# Products by Category
@app.route('/api/products', methods=['GET'])
def get_products_by_category():
    category_id = request.args.get('category_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM product WHERE category_id = {category_id}')  # Using f-string
    products = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

# Product Details
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM product WHERE product_id = {product_id}')  # Using f-string
    product = cursor.fetchone()
    conn.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(dict(product))

# Product Search
@app.route('/api/products/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM product WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'")  # Using f-string
    products = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

# Best Selling Products
@app.route('/api/products/bestsellers', methods=['GET'])
def get_best_selling_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT product.product_id, product.name, SUM(order_item.quantity) AS total_sold
        FROM order_item
        JOIN product ON product.product_id = order_item.product_id
        GROUP BY order_item.product_id
        ORDER BY total_sold DESC
        LIMIT 10
    ''')  # Using f-string
    best_sellers = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in best_sellers])

# Cart Retrieval
@app.route('/api/cart', methods=['GET'])
def get_cart():
    user_id = request.args.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Cart WHERE user_id = {user_id}')  # Using f-string
    cart = cursor.fetchone()

    if not cart:
        return jsonify({"message": "Cart is empty"}), 404

    cursor.execute(f'SELECT * FROM Cart_Item WHERE cart_id = {cart["cart_id"]}')  # Using f-string
    items = cursor.fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

# Add Item to Cart
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f'SELECT cart_id FROM Cart WHERE user_id = {data["user_id"]}')  # Using f-string
    cart = cursor.fetchone()

    # If cart doesn't exist, create a new one
    if not cart:
        cursor.execute(f'''
            INSERT INTO Cart (user_id, created_at, updated_at)
            VALUES ({data["user_id"]}, '{datetime.now()}', '{datetime.now()}')
        ''')  # Using f-string
        cart_id = cursor.lastrowid
    else:
        cart_id = cart['cart_id']
    
    # Add the item to the cart
    cursor.execute(f'''
        INSERT INTO Cart_Item (cart_id, product_id, quantity, price_per_unit)
        VALUES ({cart_id}, {data["product_id"]}, {data["quantity"]}, {data["price_per_unit"]})
    ''')  # Using f-string
    conn.commit()
    conn.close()
    return jsonify({"message": "Item added to cart successfully!"}), 201

# User Orders Retrieval
@app.route('/api/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Order WHERE user_id = {user_id}')  # Using f-string
    orders = cursor.fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
