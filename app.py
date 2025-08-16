from flask import Flask, request, jsonify, abort
import requests
import subprocess
import time
import os
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
API_SECRET = os.environ.get('TIKA_SECRET', 'please-change-this-secret')
PORT = int(os.environ.get('PORT', 8080))
TIKA_PORT = 9998

# Global state
tika_process = None
tika_ready = False

def start_tika_server():
    """Start the Tika server in a background process"""
    global tika_process, tika_ready
    
    try:
        logger.info("Starting Apache Tika server...")
        
        # Start Tika server
        tika_process = subprocess.Popen([
            'java', '-jar', '/app/tika-server.jar',
            '--host=0.0.0.0', 
            f'--port={TIKA_PORT}',
            '--enableUnsecureFeatures',  # Required for some document types
            '--enableFileUrl'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Tika to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f'http://localhost:{TIKA_PORT}/version', timeout=2)
                if response.status_code == 200:
                    logger.info(f"Tika server ready! Version: {response.text}")
                    tika_ready = True
                    return
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"Waiting for Tika server... ({i+1}/{max_retries})")
            time.sleep(2)
        
        logger.error("Tika server failed to start within timeout period")
        
    except Exception as e:
        logger.error(f"Failed to start Tika server: {str(e)}")

def validate_api_key():
    """Validate the API key from request headers"""
    provided_key = request.headers.get('X-API-Key')
    
    if not provided_key:
        abort(401, {'error': 'Missing X-API-Key header'})
    
    if provided_key != API_SECRET:
        abort(401, {'error': 'Invalid API key'})

@app.route('/')
def index():
    """Basic info endpoint"""
    return {
        'service': 'Secure Tika Server',
        'status': 'running',
        'tika_ready': tika_ready,
        'usage': {
            'endpoint': '/parse',
            'method': 'POST',
            'auth': 'X-API-Key header required',
            'content_types': 'PDF, Word, Excel, PowerPoint, etc.'
        }
    }

@app.route('/health')
def health():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy' if tika_ready else 'starting',
        'tika_ready': tika_ready,
        'timestamp': time.time()
    }
    
    status_code = 200 if tika_ready else 503
    return health_status, status_code

@app.route('/parse', methods=['POST'])
def parse_document():
    """Main document parsing endpoint"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server is still starting. Please wait and try again.'})
    
    if not request.data:
        abort(400, {'error': 'No file data provided. Send file as request body.'})
    
    try:
        # Get optional parameters
        output_format = request.args.get('format', 'text')  # text, html, or metadata
        
        # Determine Tika endpoint based on format
        if output_format == 'html':
            tika_endpoint = f'http://localhost:{TIKA_PORT}/tika'
            accept_header = 'text/html'
        elif output_format == 'metadata':
            tika_endpoint = f'http://localhost:{TIKA_PORT}/meta'
            accept_header = 'application/json'
        else:  # default to plain text
            tika_endpoint = f'http://localhost:{TIKA_PORT}/tika'
            accept_header = 'text/plain'
        
        # Forward request to Tika server
        logger.info(f"Processing document, format: {output_format}")
        
        response = requests.put(
            tika_endpoint,
            data=request.data,
            headers={
                'Accept': accept_header,
                'Content-Type': request.headers.get('Content-Type', 'application/octet-stream')
            },
            timeout=60  # Generous timeout for large documents
        )
        
        if response.status_code != 200:
            logger.error(f"Tika server error: {response.status_code} - {response.text}")
            abort(500, {'error': f'Tika processing failed: {response.status_code}'})
        
        # Prepare response
        result = {
            'success': True,
            'format': output_format,
            'content_length': len(response.text),
            'processing_time': response.elapsed.total_seconds()
        }
        
        if output_format == 'metadata':
            try:
                result['metadata'] = response.json()
            except:
                result['metadata'] = response.text
        else:
            result['content'] = response.text
        
        logger.info(f"Document processed successfully, {len(response.text)} characters extracted")
        return result
        
    except requests.exceptions.Timeout:
        logger.error("Tika processing timeout")
        abort(504, {'error': 'Document processing timeout. File may be too large or complex.'})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Tika server connection error: {str(e)}")
        abort(503, {'error': 'Tika server unavailable'})
        
    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}")
        abort(500, {'error': 'Internal server error'})

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': str(error.description)}), 401

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error.description)}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error.description)}), 500

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({'error': 'Service Unavailable', 'message': str(error.description)}), 503

if __name__ == '__main__':
    # Start Tika server in background thread
    tika_thread = threading.Thread(target=start_tika_server, daemon=True)
    tika_thread.start()
    
    # Start Flask app
    logger.info(f"Starting Flask app on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
