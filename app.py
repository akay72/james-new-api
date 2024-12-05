from flask import Flask, request, jsonify
from scraper import fetch_contact_info  # Import the scraping function

app = Flask(__name__)

@app.route('/api/fetch_contact', methods=['GET'])
def fetch_contact():
    # Get query parameters
    search_term = request.args.get('search_term')
    state_name = request.args.get('state_name')
    target_street_address = request.args.get('target_street_address', '')  # Optional parameter

    # Validate parameters
    if not search_term or not state_name or not target_street_address:
        return jsonify({"error": "Please provide all  'search_term','state_name' and 'target_street_address' parameters"}), 400

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

if __name__ == '__main__':
    # Run Flask with threading enabled for better concurrency
    app.run(debug=True, threaded=True)
