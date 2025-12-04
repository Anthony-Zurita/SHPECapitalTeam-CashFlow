"""
Lightweight Flask server for running the trading algorithm via dashboard
No complex backend needed - just a simple API endpoint
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow dashboard to call API

# Path to your algorithm (now using modular structure)
ALGORITHM_PATH = 'run_algorithm.py'
PYTHON_PATH = 'trading_env/Scripts/python.exe'

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/run-algorithm', methods=['POST'])
def run_algorithm():
    """
    Run the trading algorithm and return results
    This endpoint is called when user clicks refresh
    """
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting algorithm...")
        
        # Run the Python algorithm with UTF-8 encoding
        result = subprocess.run(
            [PYTHON_PATH, ALGORITHM_PATH],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace problematic characters instead of crashing
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Algorithm failed: {result.stderr}'
            }), 500
        
        # Read the generated JSON
        with open('output/dashboard_data/latest.json', 'r') as f:
            data = json.load(f)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Algorithm completed successfully")
        
        return jsonify({
            'success': True,
            'message': 'Algorithm completed successfully',
            'data': data
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Algorithm took too long to run (>5 minutes)'
        }), 500
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': f'File not found: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/api/latest-data', methods=['GET'])
def get_latest_data():
    """
    Get the latest data without running algorithm
    This is the original refresh behavior
    """
    try:
        with open('output/dashboard_data/latest.json', 'r') as f:
            data = json.load(f)
        return jsonify({
            'success': True,
            'data': data
        })
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'No data available. Run algorithm first.'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/output/dashboard_data/<path:filename>')
def serve_json(filename):
    """Serve JSON files"""
    return send_from_directory('output/dashboard_data', filename)

@app.route('/background.jpg')
def serve_background():
    """Serve background image"""
    return send_from_directory('.', 'background.jpg')

@app.route('/loading.gif')
def serve_loading_gif():
    """Serve loading GIF"""
    return send_from_directory('.', 'loading.gif')

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SHPE Capital Trading Dashboard Server")
    print("=" * 60)
    print(f"Dashboard: http://localhost:5000")
    print(f"Algorithm: {ALGORITHM_PATH}")
    print("=" * 60)
    app.run(debug=True, port=5000)
