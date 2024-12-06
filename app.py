from flask import Flask, request, jsonify
from scraper import fetch_contact_info  # Import the scraping function

app = Flask(__name__)

# Static users and API keys
users = {
    "User1": {"api_key": "a1b2c3d4e5f6g7h8", "usage_count": 0},
    "User2": {"api_key": "i9j0k1l2m3n4o5p6", "usage_count": 0},
    "User3": {"api_key": "q7r8s9t0u1v2w3x4", "usage_count": 0},
    "User4": {"api_key": "y5z6a7b8c9d0e1f2", "usage_count": 0},
    "User5": {"api_key": "g3h4i5j6k7l8m9n0", "usage_count": 0},
    "User6": {"api_key": "o1p2q3r4s5t6u7v8", "usage_count": 0},
    "User7": {"api_key": "w9x0y1z2a3b4c5d6", "usage_count": 0},
    "User8": {"api_key": "e7f8g9h0i1j2k3l4", "usage_count": 0},
    "User9": {"api_key": "m5n6o7p8q9r0s1t2", "usage_count": 0},
    "User10": {"api_key": "u3v4w5x6y7z8a9b0", "usage_count": 0},
}

# Middleware to validate API key
def validate_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({"error": "API key is required"}), 403
        
        # Check if the API key matches any user
        user = next((u for u, v in users.items() if v['api_key'] == api_key), None)
        if not user:
            return jsonify({"error": "Invalid API key"}), 403
        
        # Increment usage count
        users[user]['usage_count'] += 1
        return func(*args, **kwargs)
    return wrapper

@app.route('/api/fetch_contact', methods=['GET'])
@validate_api_key
def fetch_contact():
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
    return jsonify(users), 200

if __name__ == '__main__':
    # Run Flask with threading enabled for better concurrency
    app.run(debug=True, threaded=True)
