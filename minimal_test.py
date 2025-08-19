#!/usr/bin/env python3
"""
Minimal Flask test to check if the server works
"""

from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'working', 'message': 'Flask server is running!'})

def start_server():
    app.run(debug=False, host='localhost', port=5000, use_reloader=False)

def test_server():
    time.sleep(2)  # Wait for server to start
    try:
        response = requests.get('http://localhost:5000/api/test', timeout=5)
        print(f"Test response: {response.status_code}")
        if response.status_code == 200:
            print(f"Response data: {response.json()}")
            print("✅ Minimal Flask test successful!")
        else:
            print("❌ Unexpected response code")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test the server
    test_server()
    
    print("Press Ctrl+C to exit...")
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass