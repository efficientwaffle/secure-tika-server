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
        
        # Start Tika server with full features enabled
        tika_process = subprocess.Popen([
            'java', '-jar', '/app/tika-server.jar',
            '--host=0.0.0.0', 
            f'--port={TIKA_PORT}',
            '--enableUnsecureFeatures',  # Required for some document types
            '--enableFileUrl',
            '--enableOcr'  # Enable OCR capabilities
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Tika to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f'http://localhost:{TIKA_PORT}/version', timeout=2)
                if response.status_code == 200:
                    logger.info(f"Tika server ready! Version: {response.text.strip()}")
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
        'service': 'Secure Tika Server (Latest Version)',
        'status': 'running',
        'tika_ready': tika_ready,
        'features': [
            'PDF, Word, Excel, PowerPoint parsing',
            'OCR for images and scanned documents',
            '1000+ supported file formats',
            'Metadata extraction',
            'Language detection',
            'MIME type detection'
        ],
        'endpoints': {
            'parse': 'POST /parse - Extract text from documents',
            'metadata': 'POST /parse?format=metadata - Extract metadata only',
            'detect': 'POST /detect - Detect document type',
            'language': 'POST /language - Detect document language',
            'version': 'GET /version - Get Tika version info',
            'types': 'GET /types - List supported formats',
            'health': 'GET /health - Health check'
        },
        'auth': 'All endpoints require X-API-Key header'
    }

@app.route('/health')
def health():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy' if tika_ready else 'starting',
        'tika_ready': tika_ready,
        'timestamp': time.time(),
        'uptime_seconds': time.time() - start_time if 'start_time' in globals() else 0
    }
    
    status_code = 200 if tika_ready else 503
    return health_status, status_code

@app.route('/version')
def version_info():
    """Get Tika server version and service info"""
    result = {
        'service': 'Secure Tika Server',
        'tika_ready': tika_ready,
        'deployment_time': time.ctime(start_time) if 'start_time' in globals() else 'Unknown'
    }
    
    if tika_ready:
        try:
            response = requests.get(f'http://localhost:{TIKA_PORT}/version', timeout=5)
            result['tika_version'] = response.text.strip()
            
            # Get supported types count
            types_response = requests.get(f'http://localhost:{TIKA_PORT}/mime-types', timeout=5)
            types_count = len(types_response.text.strip().split('\n'))
            result['supported_formats'] = types_count
            
        except Exception as e:
            result['tika_version'] = f'Unable to fetch version: {str(e)}'
    else:
        result['tika_version'] = 'Tika server starting...'
    
    return result

@app.route('/types')
def supported_types():
    """List all supported MIME types"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server not ready'})
        
    try:
        response = requests.get(f'http://localhost:{TIKA_PORT}/mime-types', timeout=10)
        types = response.text.strip().split('\n')
        return {
            'success': True,
            'supported_types': types,
            'count': len(types)
        }
    except Exception as e:
        abort(500, {'error': f'Could not get types: {str(e)}'})

@app.route('/detect', methods=['POST'])
def detect_document_type():
    """Detect document type without parsing"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server is still starting'})
    
    if not request.data:
        abort(400, {'error': 'No file data provided'})
    
    try:
        response = requests.put(
            f'http://localhost:{TIKA_PORT}/detect/stream',
            data=request.data,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=30
        )
        
        return {
            'success': True,
            'mime_type': response.text.strip(),
            'file_size': len(request.data)
        }
        
    except Exception as e:
        abort(500, {'error': f'Detection failed: {str(e)}'})

@app.route('/language', methods=['POST'])
def detect_language():
    """Detect document language"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server is still starting'})
    
    if not request.data:
        abort(400, {'error': 'No file data provided'})
    
    try:
        # First extract text, then detect language
        text_response = requests.put(
            f'http://localhost:{TIKA_PORT}/tika',
            data=request.data,
            headers={'Accept': 'text/plain'},
            timeout=30
        )
        
        if not text_response.text.strip():
            return {'success': False, 'error': 'No text could be extracted for language detection'}
        
        # Detect language from extracted text
        lang_response = requests.put(
            f'http://localhost:{TIKA_PORT}/language/stream',
            data=text_response.text.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            timeout=10
        )
        
        return {
            'success': True,
            'language': lang_response.text.strip(),
            'text_length': len(text_response.text)
        }
        
    except Exception as e:
        abort(500, {'error': f'Language detection failed: {str(e)}'})

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
        logger.info(f"Processing document, format: {output_format}, size: {len(request.data)} bytes")
        
        start_time = time.time()
        response = requests.put(
            tika_endpoint,
            data=request.data,
            headers={
                'Accept': accept_header,
                'Content-Type': request.headers.get('Content-Type', 'application/octet-stream')
            },
            timeout=120  # Generous timeout for large documents
        )
        processing_time = time.time() - start_time
        
        if response.status_code != 200:
            logger.error(f"Tika server error: {response.status_code} - {response.text}")
            abort(500, {'error': f'Tika processing failed: {response.status_code}'})
        
        # Prepare response
        result = {
            'success': True,
            'format': output_format,
            'processing_time': round(processing_time, 3),
            'file_size': len(request.data)
        }
        
        if output_format == 'metadata':
            try:
                result['metadata'] = response.json()
            except:
                result['metadata'] = response.text
                
            # Add content length info
            if isinstance(result['metadata'], dict):
                result['content_length'] = result['metadata'].get('Content-Length', 'Unknown')
        else:
            result['content'] = response.text
            result['content_length'] = len(response.text)
        
        logger.info(f"Document processed successfully in {processing_time:.3f}s, extracted {len(response.text)} characters")
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

# Error handlers
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

@app.errorhandler(504)
def gateway_timeout(error):
    return jsonify({'error': 'Gateway Timeout', 'message': str(error.description)}), 504

if __name__ == '__main__':
    # Record start time
    start_time = time.time()
    
    # Start Tika server in background thread
    logger.info("Starting Secure Tika Server...")
    tika_thread = threading.Thread(target=start_tika_server, daemon=True)
    tika_thread.start()
    
    # Start Flask app
    logger.info(f"Starting Flask app on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
