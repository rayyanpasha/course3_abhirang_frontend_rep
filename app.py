import sqlite3
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your_secret_key'  # Change this to a secret key
jwt = JWTManager(app)

# DB Initialization (connect to SQLite)
def get_db():
    conn = sqlite3.connect('AbhiRang.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn


# ------------------------ User Authentication ------------------------

# User Registration
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    phone_number = data.get('phone_number')
    user_type = data.get('user_type')  # 'buyer', 'artist', 'admin'

    if not username or not password or not email:
        return jsonify({'error': 'Required fields missing'}), 400

    # Hash the password before storing
    password_hash = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO "user" (username, password_hash, email, phone_number, user_type, is_verified)
                      VALUES (?, ?, ?, ?, ?, 0)''', (username, password_hash, email, phone_number, user_type))
    conn.commit()

    return jsonify({'message': 'User registered successfully'}), 201


# User Login
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "user" WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password_hash'], password):
        access_token = jwt.create_access_token(identity=user['user_id'])
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


# ------------------------ Product Management ------------------------

# Get Products by Category or Search
@app.route('/api/products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id')
    query = request.args.get('query')

    conn = get_db()
    cursor = conn.cursor()

    if category_id:
        cursor.execute('''SELECT * FROM "product" WHERE category_id = ?''', (category_id,))
    elif query:
        cursor.execute('''SELECT * FROM "product" WHERE name LIKE ?''', ('%' + query + '%',))
    else:
        cursor.execute('SELECT * FROM "product"')

    products = cursor.fetchall()
    return jsonify([dict(product) for product in products])


# Get product details
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "product" WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(dict(product))


# ------------------------ Cart Management ------------------------

# Add item to cart
@app.route('/api/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT cart_id FROM "Cart" WHERE user_id = ?''', (user_id,))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute('''INSERT INTO "Cart" (user_id, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)''', (user_id,))
        conn.commit()
        cart_id = cursor.lastrowid
    else:
        cart_id = cart[0]

    cursor.execute('''INSERT INTO "Cart_Item" (cart_id, product_id, quantity, price_per_unit)
                      VALUES (?, ?, ?, ?)''', (cart_id, product_id, quantity, 100))  # Example price per unit
    conn.commit()

    return jsonify({'message': 'Item added to cart'}), 200


# Get user's cart
@app.route('/api/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT ci.cart_item_id, p.name, ci.quantity, ci.price_per_unit 
                      FROM "Cart_Item" ci 
                      JOIN "product" p ON ci.product_id = p.product_id
                      JOIN "Cart" c ON ci.cart_id = c.cart_id
                      WHERE c.user_id = ?''', (user_id,))
    cart_items = cursor.fetchall()

    return jsonify([dict(item) for item in cart_items])


# ------------------------ Order Management ------------------------

# Create an order
@app.route('/api/order', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    data = request.get_json()
    total_amount = data.get('total_amount')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO "Order" (user_id, order_date, total_amount, order_status)
                      VALUES (?, CURRENT_TIMESTAMP, ?, 'Pending')''', (user_id, total_amount))
    conn.commit()
    
    order_id = cursor.lastrowid
    return jsonify({'message': 'Order created successfully', 'order_id': order_id}), 201


# Get user orders
@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM "Order" WHERE user_id = ?''', (user_id,))
    orders = cursor.fetchall()

    return jsonify([dict(order) for order in orders])


# ------------------------ Reviews ------------------------

# Add review to product
@app.route('/api/review', methods=['POST'])
@jwt_required()
def add_review():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating')
    comment = data.get('comment')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO "Review" (product_id, user_id, rating, comment, created_at)
                      VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''', (product_id, user_id, rating, comment))
    conn.commit()

    return jsonify({'message': 'Review added successfully'}), 200


# ------------------------ Artist Portfolio ------------------------

# Create portfolio item (for artists)
@app.route('/api/portfolio', methods=['POST'])
@jwt_required()
def create_portfolio():
    user_id = get_jwt_identity()
    data = request.get_json()
    artwork_name = data.get('artwork_name')
    description = data.get('description')
    medium = data.get('medium')
    image_url = data.get('image_url')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO "Artist_Portfolio" (artist_id, artwork_name, description, medium, image_url, created_at)
                      VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', (user_id, artwork_name, description, medium, image_url))
    conn.commit()

    return jsonify({'message': 'Portfolio item created'}), 201


# ------------------------ Categories ------------------------

# Get all categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "category"')
    categories = cursor.fetchall()
    return jsonify([dict(category) for category in categories])


if __name__ == '__main__':
    app.run(debug=True)
