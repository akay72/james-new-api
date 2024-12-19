from flask import Flask, request, jsonify
from scraper import fetch_contact_info  # Import the scraping function
import psycopg2
from psycopg2 import sql
import os
from threading import Lock

app = Flask(__name__)

# Lock for database operations
lock = Lock()

# Database configuration (fetch from environment variable)
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize PostgreSQL database
def init_db():
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                api_key TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        # Insert static users if they don't exist
        static_users = [
            ("User1", "a1b2c3d4e5f6g7h8"),
            ("User2", "i9j0k1l2m3n4o5p6"),
            ("User3", "q7r8s9t0u1v2w3x4"),
            ("User4", "y5z6a7b8c9d0e1f2"),
            ("User5", "g3h4i5j6k7l8m9n0"),
            ("User6", "o1p2q3r4s5t6u7v8"),
            ("User7", "w9x0y1z2a3b4c5d6"),
            ("User8", "e7f8g9h0i1j2k3l4"),
            ("User9", "m5n6o7p8q9r0s1t2"),
            ("User10", "u3v4w5x6y7z8a9b0")
        ]
        for user in static_users:
            cursor.execute('''
                INSERT INTO users (username, api_key, usage_count)
                VALUES (%s, %s, 0)
                ON CONFLICT (username) DO NOTHING
            ''', user)
        conn.commit()

# Call the database initialization function on app startup
init_db()

# Middleware to validate API key
def validate_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({"error": "API key is required"}), 403

        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE api_key = %s", (api_key,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Invalid API key"}), 403

            kwargs['user'] = user[0]  # Pass the username to the route
            return func(*args, **kwargs)
    return wrapper

@app.route('/api/fetch_contact', methods=['GET'])
@validate_api_key
def fetch_contact(user):
    # Get query parameters
    search_term = request.args.get('search_term')
    state_name = request.args.get('state_name')
    target_street_address = request.args.get('target_street_address', '')  # Optional parameter

    # Validate parameters
    if not search_term or not state_name or not target_street_address:
        return jsonify({"error": "Please provide all 'search_term', 'state_name', and 'target_street_address' parameters"}), 400

    try:
        # Call the fetch_contact_info function
        data = fetch_contact_info(search_term, state_name, target_street_address)
        
        if data == "No matching company found":
            return jsonify({"message": "No company found"}), 404

        # Increment usage count in the database
        with lock, psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET usage_count = usage_count + 1
                WHERE username = %s
            ''', (user,))
            conn.commit()

        # Return the found data
        return jsonify(data), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

@app.route('/api/user_stats', methods=['GET'])
def user_stats():
    """
    Endpoint to fetch usage statistics for all users.
    """
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, api_key, usage_count FROM users")
        users = cursor.fetchall()
    return jsonify({user[0]: {"api_key": user[1], "usage_count": user[2]} for user in users}), 200

if __name__ == '__main__':
    # Run Flask with threading enabled for better concurrency
    app.run(debug=True, threaded=True)
