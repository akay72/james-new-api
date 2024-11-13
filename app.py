from flask import Flask, request, jsonify
from scraper import fetch_contact_info  # Import the scraping function

app = Flask(__name__)

@app.route('/api/fetch_contact', methods=['GET'])
def fetch_contact():
    # Get query parameters
    search_term = request.args.get('search_term')
    state_name = request.args.get('state_name')
    target_street_address = request.args.get('target_street_address')  # New parameter
    
    # Validate parameters
    if not search_term or not state_name or not target_street_address:
        return jsonify({"error": "Please provide 'search_term', 'state_name', and 'target_street_address' parameters"}), 400

    try:
        # Call the fetch_contact_info function with the new parameter and return the results
        data = fetch_contact_info(search_term, state_name, target_street_address)
        return jsonify(data), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching data", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
