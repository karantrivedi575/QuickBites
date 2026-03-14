import mysql.connector
from flask import g

# Database configuration
import os

# This helper handles empty strings or missing variables gracefully
def get_env_int(key, default):
    value = os.getenv(key)
    return int(value) if value and value.strip() else default

db_config = {
    'host': os.getenv('MYSQLHOST', 'localhost'),
    'user': os.getenv('MYSQLUSER', 'root'),
    'password': os.getenv('MYSQLPASSWORD', 'admin'),
    'database': os.getenv('MYSQLDATABASE', 'cafe'),
    'port': get_env_int('MYSQLPORT', 3306)
}
def get_db():
    """Get a database connection. Create it if it's not already connected."""
    if 'db' not in g:
        g.db = mysql.connector.connect(**db_config)
    return g.db

def get_cursor():
    """Get a cursor from the database connection."""
    db = get_db()
    return db.cursor(dictionary=True)

def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database and create tables if they do not exist."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'user'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            items TEXT NOT NULL,
            total_price DECIMAL(10, 2) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            image_url VARCHAR(255),
            stock INT DEFAULT 0,
            category VARCHAR(255)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            customer_name VARCHAR(100),
            items JSON,
            total_price DECIMAL(10, 2),
            date_issued DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_queries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()

# Initialize the database
init_db()
