import base64
import json
import logging
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store services in memory (can be replaced with a database)
running_services = []

@app.route('/eventarc', methods=['POST'])
def handle_eventarc_event():
    """Handle incoming Eventarc events."""
    try:
        # Parse Pub/Sub message from the request
        envelope = request.get_json()
        logging.debug(f"Received envelope: {json.dumps(envelope)}")

        # Extract the Pub/Sub message data
        if not envelope or 'message' not in envelope:
            raise ValueError("Invalid Pub/Sub message format")
        
        pubsub_message = envelope['message']
        if 'data' not in pubsub_message:
            raise ValueError("Pub/Sub message is missing data field")

        # Decode the base64-encoded data
        event_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
        logging.debug(f"Decoded event data: {event_data}")

        # Parse the decoded data as JSON
        event = json.loads(event_data)

        # Parse the event payload for Cloud Run service details
        log_name = event.get("protoPayload", {}).get("serviceName", "")
        service_name = event.get("protoPayload", {}).get("resourceName", "")

        # Handle service creation and deletion
        if "create" in log_name:
            running_services.append(service_name)
        elif "delete" in log_name and service_name in running_services:
            running_services.remove(service_name)

        return "Event processed", 200
    except Exception as e:
        logging.error(f"Error processing event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/services', methods=['GET'])
def list_services():
    """List tracked running services."""
    return jsonify(running_services), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
