from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_cursor, get_db
from flask_mail import Mail, Message
import mysql.connector
import json, random, string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'quickbites575@gmail.com'
app.config['MAIL_PASSWORD'] = 'euxr cmtf dntg swuf'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

reset_tokens = {}

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    token = generate_token()
    reset_tokens[email] = token

    msg = Message('Password Reset Request', sender='your_email@gmail.com', recipients=[email])
    msg.body = f'Click on the link to reset your password: {url_for("reset_password", token=token, _external=True)}'
    mail.send(msg)

    flash('Password reset link sent to your email!', 'info')
    return redirect(url_for('index'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = next((k for k, v in reset_tokens.items() if v == token), None)
    if not email:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        if not new_password:
            flash('Password cannot be empty', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        hashed_password = generate_password_hash(new_password)
        try:
            cursor = get_cursor()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            get_db().commit()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()

        reset_tokens.pop(email, None)
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('reset_password.html', token=token)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone_no = request.form.get('phone_no')

    if not name or not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('index'))

    if phone_no and len(phone_no) < 10:
        flash('Invalid phone number. It should be at least 10 digits.', 'error')
        return redirect(url_for('index'))

    hashed_password = generate_password_hash(password)

    try:
        cursor = get_cursor()
        cursor.execute('''
            INSERT INTO users (name, email, password, phone_no, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, email, hashed_password, phone_no, 'user'))
        get_db().commit()
        cursor.close()

        flash('Signup successful! You can now login.', 'success')

    except Exception:
        flash('Email is already registered. Please use a different email.', 'error')
        return redirect(url_for('index'))

    return redirect(url_for('index'))



# Login route to handle login form
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cursor = get_cursor()
    cursor.execute('SELECT id, password, role FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()

    if user is None:
        flash('No account found with that email. Please sign up.', 'danger')
        return redirect(url_for('index'))

    stored_password_hash = user['password']
    
    if check_password_hash(stored_password_hash, password):
        session['logged_in'] = True
        session['role'] = user['role']
        session['user_id'] = user['id']

        flash('Login successful', 'success')

        if session['role'] == 'admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_user'))
    else:
        flash('Invalid email or password', 'danger')

    cursor.close()
    return redirect(url_for('index'))


@app.route('/dashboard_admin')
def dashboard_admin():
    if 'logged_in' in session and session.get('role') == 'admin':
        return render_template('dashboard.html', role=session['role'])
    else:
        flash('You need to log in as admin to access this page.', 'danger')
        return redirect(url_for('login'))


@app.route('/dashboard_user')
def dashboard_user():
    if 'logged_in' in session and session.get('role') == 'user':
        return render_template('dashboard.html', role=session['role'])
    else:
        flash('You need to log in as a user to access this page.', 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('logged_in', None)
    flash('You have been logged out!', 'success')
    return redirect(url_for('index'))


@app.route('/products')
def products():
    cursor = get_cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    cursor.close()

    user_role = session.get('role', 'user')

    return render_template('products.html', products=products, user_role=user_role)


@app.route('/help')
def help_page():
    return render_template('help.html')


@app.route('/submit-help-query', methods=['POST'])
def submit_help_query():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    cursor = get_cursor()
    query = "INSERT INTO support_queries (name, email, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, email, message))
    get_db().commit()
    cursor.close()

    flash('Your message has been submitted successfully!', 'success')
    return redirect(url_for('help_page'))  


# Route to manage products (only accessible to admin)
@app.route('/manage')
def manage():
    if 'logged_in' in session and session['role'] == 'admin':
        cursor = get_cursor()
        
        # Fetch products, completed orders, and invoices
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()

        cursor.execute("SELECT id, total_price FROM orders WHERE status='completed'")
        completed_orders = cursor.fetchall()

        cursor.execute("SELECT id, total_price, date_issued FROM invoices")
        invoices = cursor.fetchall()

        cursor.close()
        
        return render_template('manage.html', products=products, completed_orders=completed_orders, invoices=invoices)
    else:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

# Helper function to fetch all products
def get_all_products():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    return products

# Helper function to fetch low-stock products
def get_low_stock_products(threshold=10):
    cursor = get_cursor()
    cursor.execute("SELECT * FROM products WHERE stock < %s", (threshold,))
    low_stock_products = cursor.fetchall()
    cursor.close()
    return low_stock_products

# Route for product management
@app.route('/product_management')
def product_management():
    products = get_all_products()
    low_stock_products = get_low_stock_products()
    return render_template('product_management.html', products=products, low_stock_products=low_stock_products)

# Route to update product information
@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    try:
        data = request.get_json()

        # Debugging: Print received data
        print("Received data:", data)

        cursor = get_cursor()
        query = """
            UPDATE products
            SET url = %s, name = %s, description = %s, price = %s, stock = %s, category = %s
            WHERE id = %s
        """
        cursor.execute(query, (data['url'], data['name'], data['description'], data['price'], data['stock'], data['category'], product_id))
        get_db().commit()

        if cursor.rowcount > 0:
            print(f"Product {product_id} updated successfully.")
        else:
            print(f"No rows were updated. Product {product_id} may not exist.")

        cursor.close()
        flash('Product updated successfully!', 'success')
        return jsonify(success=True)

    except Exception as e:
        print(f"Error updating product: {e}")
        flash(f"Error updating product: {e}", 'error')
        return jsonify(success=False, error=str(e))

# Route to delete a product
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    cursor = get_cursor()
    query = "DELETE FROM products WHERE id = %s"
    cursor.execute(query, (product_id,))
    get_db().commit()
    cursor.close()

    return jsonify(success=True)


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()

        # Insert the new product into the database
        cursor = get_cursor()
        query = """
            INSERT INTO products (url, name, description, price, stock, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (data['url'], data['name'], data['description'], data['price'], data['stock'], data['category']))
        get_db().commit()

        new_product_id = cursor.lastrowid
        cursor.close()

        flash('New product added successfully!', 'success')
        return jsonify(success=True, product_id=new_product_id)

    except Exception as e:
        print(f"Error adding product: {e}")
        flash(f"Error adding product: {e}", 'error')
        return jsonify(success=False, error=str(e))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('You need to be logged in to make a purchase!', 'error')
        return redirect(url_for('login'))

    cursor = get_cursor()
    
    cursor.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('login'))

    customer_name = user['name']

    if request.method == 'POST':
        cart_data = request.json
        if not cart_data or 'items' not in cart_data:
            return jsonify({'success': False, 'error': 'No items in the cart'}), 400

        cart_items = cart_data['items']
        payment_method = cart_data.get('paymentMethod')

        total_price = 0
        updated_cart_items = []

        try:
            for item in cart_items:
                if 'id' not in item or 'quantity' not in item:
                    return jsonify({'success': False, 'error': 'Invalid cart item data'}), 400

                product_id = item['id']
                quantity = item['quantity']

                cursor.execute('SELECT name, price, stock FROM products WHERE id = %s', (product_id,))
                product = cursor.fetchone()

                if not product:
                    return jsonify({'success': False, 'error': f'Product with ID {product_id} not found'}), 400

                name = product['name']
                price = float(product['price'])
                stock = product['stock']

                if stock < quantity:
                    return jsonify({'success': False, 'error': f'Not enough stock for product {product_id}'}), 400

                total_price += price * quantity
                item['name'] = name
                item['price'] = price
                updated_cart_items.append(item)

            cursor.execute(''' 
                INSERT INTO orders (items, total_price, status, customer_id, customer_name, payment_method) 
                VALUES (%s, %s, %s, %s, %s, %s) 
            ''', (json.dumps(updated_cart_items), float(total_price), 'pending', session['user_id'], customer_name, payment_method))

            for item in updated_cart_items:
                cursor.execute('UPDATE products SET stock = stock - %s WHERE id = %s', (item['quantity'], item['id']))

            get_db().commit()

        except Exception as e:
            print("Error processing checkout:", e)
            get_db().rollback()
            return jsonify({'success': False, 'error': 'An error occurred while processing your order'}), 500
        finally:
            cursor.close()

        return jsonify({'success': True, 'message': 'Thank you for your purchase!', 'total_price': total_price})

    return render_template('checkout.html')


@app.route('/order_management', methods=['GET'])
def order_management():
    cursor = get_cursor()

    # Fetch all orders with customer information
    cursor.execute('''
        SELECT orders.id AS order_id, orders.items, orders.total_price, orders.status, 
               users.id AS customer_id, users.name AS customer_name, users.email AS customer_email, users.phone_no AS customer_phone
        FROM orders
        JOIN users ON orders.customer_id = users.id
    ''')
    orders = cursor.fetchall()

    orders_with_items = []
    for order in orders:
        try:
            if order['items']:
                order_items = json.loads(order['items'])
                order['items'] = order_items
            else:
                order['items'] = []
            orders_with_items.append(order)
        except json.JSONDecodeError:
            order['items'] = []

    cursor.close()
    return render_template('order_management.html', orders_with_items=orders_with_items)


@app.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    new_status = request.form.get('status')

    if new_status:
        try:
            cursor = get_cursor()
            cursor.execute('''UPDATE orders SET status = %s WHERE id = %s''', (new_status, order_id))
            get_db().commit()
            flash('Order status updated successfully!', 'success')
        except Exception as e:
            flash(f"Error updating status: {e}", 'error')
        finally:
            cursor.close()

    return redirect(url_for('order_management'))


@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    cursor = get_cursor()
    cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
    get_db().commit()
    cursor.close()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('order_management'))


def get_invoices():
    try:
        cursor = get_cursor()
        cursor.execute("SELECT id, order_id, customer_name, total_price, date_issued FROM invoices")
        invoices = cursor.fetchall()
        return invoices
    except Exception as e:
        print(f"Error fetching invoices: {e}")
        return []


def get_completed_orders():
    cursor = get_cursor()
    cursor.execute("SELECT id, total_price FROM orders WHERE status = 'completed'")
    return cursor.fetchall()


@app.route('/billing')
def billing():
    try:
        invoices = get_invoices()
        completed_orders = get_completed_orders()
        return render_template('billing.html', invoices=invoices, completed_orders=completed_orders)
    except Exception as e:
        print(f"Error loading billing page: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Route to get completed orders
@app.route('/completed_orders', methods=['GET'])
def completed_orders():
    try:
        cursor = get_cursor()
        cursor.execute("SELECT id, total_price FROM orders WHERE status = 'completed'")
        orders = cursor.fetchall()

        if not orders:
            return jsonify({'orders': []})

        # Format orders as a list of dictionaries, converting total_price to float
        order_list = []
        for order in orders:
            order_id = order['id']
            total_price_str = order['total_price']

            try:
                total_price = float(total_price_str)
                order_list.append({'id': order_id, 'total_price': total_price})
            except ValueError:
                print(f"Skipping order {order_id} due to invalid total_price: {total_price_str}")

        return jsonify({'orders': order_list})

    except Exception as e:
        print("Error fetching completed orders:")
        
        return jsonify({'error': 'Internal server error'}), 500


# Route to generate an invoice for a specific order
@app.route('/generate_invoice/<int:order_id>', methods=['POST'])
def generate_invoice(order_id):
    try:
        cursor = get_cursor()

        # Fetch order details based on order_id
        cursor.execute("""
            SELECT o.items, o.total_price, u.name AS customer_name
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE o.id = %s
        """, (order_id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        items = json.loads(order['items'])
        total_price = order['total_price']
        customer_name = order['customer_name']

        # Insert into the invoices table
        cursor.execute(""" 
            INSERT INTO invoices (order_id, customer_name, items, total_price) 
            VALUES (%s, %s, %s, %s)
        """, (order_id, customer_name, json.dumps(items), total_price))

        get_db().commit()
        invoice_id = cursor.lastrowid

        # Update the order status to indicate it has been invoiced
        cursor.execute("UPDATE orders SET status = 'invoiced' WHERE id = %s", (order_id,))
        get_db().commit()

        # Fetch the newly created invoice details
        cursor.execute("SELECT id, total_price, date_issued FROM invoices WHERE id = %s", (invoice_id,))
        new_invoice = cursor.fetchone()

        # Prepare the response
        response = {
            'new_invoice': {
                'id': new_invoice['id'],
                'total_price': new_invoice['total_price'],
                'date_issued': new_invoice['date_issued'].strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': 'Invoice generated successfully',
            'remove_order_id': order_id
        }

        return jsonify(response), 201

    except Exception as e:
        print(f"Error generating invoice: {e}")
        
        return jsonify({'error': 'Internal server error'}), 500

# Route to view a specific invoice
@app.route('/view_invoice/<int:invoice_id>', methods=['GET'])
def view_invoice(invoice_id):
    try:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = %s", (invoice_id,))
        invoice = cursor.fetchone()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        # Format the response
        invoice_data = {
            'id': invoice['id'],
            'order_id': invoice['order_id'],  # Include the order ID
            'customer_name': invoice['customer_name'],  # Retrieve customer name
            'items': json.loads(invoice['items']),  # Parse items JSON
            'total_price': invoice['total_price'],  # Total price of the invoice
            'date_issued': invoice['date_issued'].isoformat()  # Format date for JSON serialization
        }
        for item in invoice_data['items']:
    # Ensure the item has a quantity; this might come from another source or be set earlier
    # For example, if your items are originally created with quantities in a different table:
    # item['quantity'] = get_item_quantity(item_id)  # Hypothetical function

    # If the quantity isn't already part of the item data structure, you'll need to add it.
    # This example assumes each item in the JSON string has the 'quantity' field.
         if 'quantity' not in item:
            item['quantity'] = 1  # Default to 1 if no quantity is specified

        return jsonify(invoice_data), 200  # Return the invoice data with 200 OK

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500  # Return 500 Internal Server Error

@app.route('/queries')
def queries():
    """Fetch and display support queries."""
    cursor = get_cursor()
    
    cursor.execute("SELECT id, name, email, message, created_at FROM support_queries")
    queries = cursor.fetchall()
    
    cursor.close()
    
    return render_template('queries.html', queries=queries)

@app.route('/reply_query/<int:query_id>', methods=['POST'])
def reply_query(query_id):
    """Send a reply to the user's query."""
    reply_message = request.form['reply_message']
    cursor = get_cursor()
    cursor.execute("SELECT email FROM support_queries WHERE id = %s", (query_id,))
    user_email = cursor.fetchone()
    
    if user_email:
        # Implement your email sending logic here
        flash('Reply sent successfully!', 'success')
    else:
        flash('Error sending reply. User not found.', 'danger')
    
    cursor.close()
    return redirect(url_for('queries'))


# Start the application
if __name__ == '__main__':
    app.run(debug=True)

