from flask import Flask, request, jsonify
from scrapper import fetch_contact_info  # Import the scraping function

app = Flask(__name__)

@app.route('/api/fetch_contact', methods=['GET'])
def fetch_contact():
    # Get query parameters
    search_term = request.args.get('search_term')
    state_name = request.args.get('state_name')
    
    # Validate parameters
    if not search_term or not state_name:
        return jsonify({"error": "Please provide both 'search_term' and 'state_name' parameters"}), 400

    try:
        # Call the fetch_contact_info function and return the results
        data = fetch_contact_info(search_term, state_name)
        return jsonify(data), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching data", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
