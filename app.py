import jwt
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE = 'AbhiRang.db'  

# Get secret key from environment variable or hardcode (in real applications, use environment variables)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key_here")
JWT_EXPIRATION_DELTA = timedelta(days=1)  # Token expiry time

# Helper functions
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

# Helper function to generate JWT token
def generate_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

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
        cursor.execute('''
            INSERT INTO "user" (username, password_hash, email, phone_number, user_type, is_verified)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['username'], password_hash, data['email'], data['phone_number'], data['user_type'], is_verified))
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

    # Generate JWT token
    token = generate_jwt_token(user['user_id'])

    return jsonify({"message": "Login successful!", "token": token}), 200

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    # Verify JWT token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token is missing!"}), 401

    try:
        # Strip "Bearer " from the token string
        token = token.split(" ")[1]
        decoded_token = jwt.decode(token, "JWT_SECRET_KEY", algorithms=["HS256"])

        user_id = decoded_token['user_id']  # Extract user ID from the token

        # Now you can proceed with adding the item to the cart, using the user_id
        data = request.get_json()
        product_id = data["product_id"]
        quantity = data["quantity"]
        price_per_unit = data["price_per_unit"]

        # Check if the cart exists for the user, otherwise create it
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT cart_id FROM Cart WHERE user_id = ?', (user_id,))
        cart = cursor.fetchone()

        if not cart:
            cursor.execute('''
                INSERT INTO Cart (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
            ''', (user_id, datetime.datetime.now(), datetime.datetime.now()))
            cart_id = cursor.lastrowid
        else:
            cart_id = cart['cart_id']

        # Add item to cart
        cursor.execute('''
            INSERT INTO Cart_Item (cart_id, product_id, quantity, price_per_unit)
            VALUES (?, ?, ?, ?)
        ''', (cart_id, product_id, quantity, price_per_unit))
        conn.commit()
        conn.close()

        return jsonify({"message": "Item added to cart successfully!"}), 201

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired!"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token!"}), 401
# Protect routes with JWT
@app.route('/api/protected', methods=['GET'])
def protected_route():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({"error": "Token is missing"}), 403

    try:
        decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    return jsonify({"message": f"Hello User {user_id}, you're authorized!"})

# Other Routes (No Change Needed for JWT)
# ... your existing routes here (categories, products, etc.)

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
    cursor.execute(f'SELECT * FROM product WHERE category_id = ?', (category_id,))
    products = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

# Product Details
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM product WHERE product_id = ?', (product_id,))
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
    cursor.execute(f"SELECT * FROM product WHERE name LIKE ? OR description LIKE ?", (f'%{query}%', f'%{query}%'))
    products = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

# Best Selling Products
@app.route('/api/products/bestsellers', methods=['GET'])
def get_best_selling_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT product.product_id, product.name, SUM(order_item.quantity) AS total_sold
        FROM order_item
        JOIN product ON product.product_id = order_item.product_id
        GROUP BY order_item.product_id
        ORDER BY total_sold DESC
        LIMIT 10
    ''')
    best_sellers = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in best_sellers])

# Cart Retrieval


# User Orders Retrieval
@app.route('/api/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Order WHERE user_id = ?', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders])

# Order Details
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Order_Item WHERE order_id = ?', (order_id,))
    order_items = cursor.fetchall()
    conn.close()

    if not order_items:
        return jsonify({"error": "Order not found"}), 404

    return jsonify([dict(item) for item in order_items])

# Artist Portfolio
@app.route('/api/portfolio', methods=['GET'])
def get_artist_portfolio():
    artist_id = request.args.get('artist_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Artist_Portfolio WHERE artist_id = ?', (artist_id,))
    portfolio = cursor.fetchall()
    conn.close()
    return jsonify([dict(item) for item in portfolio])

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    # Check if the product exists in the cart
    cursor.execute('SELECT * FROM Cart_Item WHERE cart_id = ? AND product_id = ?',
                   (data['cart_id'], data['product_id']))
    cart_item = cursor.fetchone()

    if cart_item:
        # Update the quantity
        cursor.execute('UPDATE Cart_Item SET quantity = ? WHERE cart_id = ? AND product_id = ?',
                       (data['quantity'], data['cart_id'], data['product_id']))
    else:
        # Add new item to cart if it doesn't exist
        cursor.execute('''
            INSERT INTO Cart_Item (cart_id, product_id, quantity, price_per_unit)
            VALUES (?, ?, ?, ?)
        ''', (data['cart_id'], data['product_id'], data['quantity'], data['price_per_unit']))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Cart updated successfully!"}), 200

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM Cart_Item WHERE cart_id = ? AND product_id = ?',
                   (data['cart_id'], data['product_id']))

    conn.commit()
    conn.close()
    return jsonify({"message": "Item removed from cart!"}), 200


@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data['user_id']

    # Create a new order
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO "Order" (user_id, order_date, total_amount)
        VALUES (?, ?, ?)
    ''', (user_id, datetime.now(), data['total_amount']))
    order_id = cursor.lastrowid

    # Add items to the order
    for item in data['items']:
        cursor.execute('''
            INSERT INTO "Order_Item" (order_id, product_id, quantity, price_per_unit)
            VALUES (?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['quantity'], item['price_per_unit']))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Order created successfully!"}), 201


@app.route('/api/orders/status/<int:order_id>', methods=['GET', 'POST'])
def order_status(order_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT status FROM "Order" WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()

        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        return jsonify({"status": order["status"]}), 200

    elif request.method == 'POST':
        new_status = request.get_json()['status']
        cursor.execute('UPDATE "Order" SET status = ? WHERE order_id = ?',
                       (new_status, order_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Order status updated successfully!"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
