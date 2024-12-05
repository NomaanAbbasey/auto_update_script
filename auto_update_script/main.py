import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store services in memory (can be replaced with a database)
running_services = []

@app.route('/eventarc', methods=['POST'])
def handle_eventarc_event():
    """Handle incoming Eventarc events."""
    try:
        event = request.get_json()
        # Parse the event payload for Cloud Run service details
        log_name = event.get("protoPayload", {}).get("serviceName")
        service_name = event.get("protoPayload", {}).get("resourceName", "")

        # Handle service creation and deletion
        if "create" in log_name:
            running_services.append(service_name)
        elif "delete" in log_name and service_name in running_services:
            running_services.remove(service_name)

        return "Event processed", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/services', methods=['GET'])
def list_services():
    """List tracked running services."""
    return jsonify(running_services), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))