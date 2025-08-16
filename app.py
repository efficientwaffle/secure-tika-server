from flask import Flask, request, jsonify, abort
import requests
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
tika_ready = False
start_time = time.time()

def check_tika_server():
    """Check if Tika server is running and ready"""
    global tika_ready
    
    try:
        logger.info("Checking Tika server status...")
        
        # The official Docker image should have Tika already running
        # We just need to wait for it to be ready
        max_retries = 60  # Longer timeout for full Tika server
        for i in range(max_retries):
            try:
                response = requests.get(f'http://localhost:{TIKA_PORT}/version', timeout=3)
                if response.status_code == 200:
                    version = response.text.strip()
                    logger.info(f"✅ Tika server ready! Version: {version}")
                    tika_ready = True
                    
                    # Also check available parsers
                    try:
                        parsers_response = requests.get(f'http://localhost:{TIKA_PORT}/parsers', timeout=5)
                        if parsers_response.status_code == 200:
                            logger.info("✅ Tika parsers loaded successfully")
                    except:
                        logger.warning("Could not verify parsers, but server is running")
                    
                    return
                    
            except requests.exceptions.RequestException:
                pass
            
            if i % 10 == 0:  # Log every 10 attempts
                logger.info(f"⏳ Waiting for Tika server... ({i+1}/{max_retries})")
            time.sleep(1)
        
        logger.error("❌ Tika server failed to become ready within timeout period")
        
    except Exception as e:
        logger.error(f"❌ Error checking Tika server: {str(e)}")

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
        'service': 'Secure Tika Server (Full Version)',
        'status': 'running',
        'tika_ready': tika_ready,
        'version': 'Official Apache Docker Image',
        'features': [
            'Full Tika server with all parsers',
            'PDF, Word, Excel, PowerPoint parsing',
            'OCR for images and scanned documents',
            '1400+ supported file formats',
            'Scientific document formats',
            'Audio/video metadata extraction',
            'Advanced text extraction',
            'Metadata extraction',
            'Language detection',
            'MIME type detection'
        ],
        'endpoints': {
            'parse': 'POST /parse - Extract text from documents',
            'metadata': 'POST /parse?format=metadata - Extract metadata only',
            'html': 'POST /parse?format=html - Extract HTML formatted text',
            'detect': 'POST /detect - Detect document type',
            'language': 'POST /language - Detect document language',
            'version': 'GET /version - Get Tika version info',
            'parsers': 'GET /parsers - List available parsers',
            'types': 'GET /types - List supported formats',
            'health': 'GET /health - Health check'
        },
        'auth': 'Most endpoints require X-API-Key header (except /, /health, /version)'
    }

@app.route('/health')
def health():
    """Health check endpoint"""
    uptime = time.time() - start_time
    health_status = {
        'status': 'healthy' if tika_ready else 'starting',
        'tika_ready': tika_ready,
        'timestamp': time.time(),
        'uptime_seconds': round(uptime, 1),
        'uptime_human': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s"
    }
    
    status_code = 200 if tika_ready else 503
    return health_status, status_code

@app.route('/version')
def version_info():
    """Get Tika server version and service info"""
    result = {
        'service': 'Secure Tika Server (Full Version)',
        'docker_image': 'apache/tika:3.2.2.0-full',
        'tika_ready': tika_ready,
        'deployment_time': time.ctime(start_time)
    }
    
    if tika_ready:
        try:
            # Get Tika version
            response = requests.get(f'http://localhost:{TIKA_PORT}/version', timeout=5)
            if response.status_code == 200:
                result['tika_version'] = response.text.strip()
            
            # Get supported types count
            types_response = requests.get(f'http://localhost:{TIKA_PORT}/mime-types', timeout=10)
            if types_response.status_code == 200:
                types_count = len(types_response.text.strip().split('\n'))
                result['supported_formats'] = types_count
            
            # Get parsers count
            parsers_response = requests.get(f'http://localhost:{TIKA_PORT}/parsers', timeout=10)
            if parsers_response.status_code == 200:
                result['available_parsers'] = 'Available via /parsers endpoint'
                
        except Exception as e:
            result['tika_version'] = f'Unable to fetch details: {str(e)}'
    else:
        result['tika_version'] = 'Tika server starting...'
    
    return result

@app.route('/parsers')
def available_parsers():
    """Get list of available parsers (public endpoint)"""
    if not tika_ready:
        abort(503, {'error': 'Tika server not ready'})
        
    try:
        response = requests.get(f'http://localhost:{TIKA_PORT}/parsers', timeout=10)
        if response.status_code == 200:
            return {
                'success': True,
                'parsers': response.text,
                'note': 'This shows all available parsers in the full Tika server'
            }
        else:
            abort(500, {'error': f'Failed to get parsers: HTTP {response.status_code}'})
            
    except Exception as e:
        abort(500, {'error': f'Could not get parsers: {str(e)}'})

@app.route('/types')
def supported_types():
    """List all supported MIME types"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server not ready'})
        
    try:
        response = requests.get(f'http://localhost:{TIKA_PORT}/mime-types', timeout=10)
        if response.status_code == 200:
            types = response.text.strip().split('\n')
            return {
                'success': True,
                'supported_types': types,
                'count': len(types)
            }
        else:
            abort(500, {'error': f'Failed to get types: HTTP {response.status_code}'})
            
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
        
        if response.status_code == 200:
            return {
                'success': True,
                'mime_type': response.text.strip(),
                'file_size': len(request.data)
            }
        else:
            abort(500, {'error': f'Detection failed: HTTP {response.status_code}'})
        
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
            timeout=60
        )
        
        if text_response.status_code != 200:
            abort(500, {'error': f'Text extraction failed: HTTP {text_response.status_code}'})
        
        if not text_response.text.strip():
            return {'success': False, 'error': 'No text could be extracted for language detection'}
        
        # Detect language from extracted text
        lang_response = requests.put(
            f'http://localhost:{TIKA_PORT}/language/stream',
            data=text_response.text.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            timeout=10
        )
        
        if lang_response.status_code == 200:
            return {
                'success': True,
                'language': lang_response.text.strip(),
                'text_length': len(text_response.text),
                'confidence': 'Language detection completed'
            }
        else:
            abort(500, {'error': f'Language detection failed: HTTP {lang_response.status_code}'})
        
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
    
    # Check file size (limit to 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if len(request.data) > max_size:
        abort(413, {'error': f'File too large. Maximum size is {max_size // (1024*1024)}MB'})
    
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
        logger.info(f"Processing document: format={output_format}, size={len(request.data)} bytes")
        
        start_processing = time.time()
        response = requests.put(
            tika_endpoint,
            data=request.data,
            headers={
                'Accept': accept_header,
                'Content-Type': request.headers.get('Content-Type', 'application/octet-stream')
            },
            timeout=300  # 5 minutes for very large documents
        )
        processing_time = time.time() - start_processing
        
        if response.status_code != 200:
            logger.error(f"Tika server error: {response.status_code} - {response.text[:500]}")
            abort(500, {'error': f'Tika processing failed: HTTP {response.status_code}'})
        
        # Prepare response
        result = {
            'success': True,
            'format': output_format,
            'processing_time': round(processing_time, 3),
            'file_size': len(request.data),
            'server_version': 'Full Tika Server'
        }
        
        if output_format == 'metadata':
            try:
                result['metadata'] = response.json()
                # Add some metadata stats
                if isinstance(result['metadata'], dict):
                    result['metadata_fields'] = len(result['metadata'])
            except:
                result['metadata'] = response.text
                
        else:
            result['content'] = response.text
            result['content_length'] = len(response.text)
            
            # Add some basic text analysis
            if response.text:
                lines = response.text.split('\n')
                words = response.text.split()
                result['text_stats'] = {
                    'lines': len(lines),
                    'words': len(words),
                    'characters': len(response.text)
                }
        
        logger.info(f"✅ Document processed successfully in {processing_time:.3f}s")
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

# Advanced endpoint for comprehensive analysis
@app.route('/analyze', methods=['POST'])
def analyze_document():
    """Comprehensive document analysis (text + metadata + type detection)"""
    validate_api_key()
    
    if not tika_ready:
        abort(503, {'error': 'Tika server not ready'})
    
    if not request.data:
        abort(400, {'error': 'No file data provided'})
    
    try:
        start_time = time.time()
        results = {}
        
        # 1. Detect document type
        logger.info("Analyzing document: detecting type...")
        detect_response = requests.put(
            f'http://localhost:{TIKA_PORT}/detect/stream',
            data=request.data,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=30
        )
        
        if detect_response.status_code == 200:
            results['mime_type'] = detect_response.text.strip()
        
        # 2. Extract metadata
        logger.info("Analyzing document: extracting metadata...")
        metadata_response = requests.put(
            f'http://localhost:{TIKA_PORT}/meta',
            data=request.data,
            headers={'Accept': 'application/json'},
            timeout=120
        )
        
        if metadata_response.status_code == 200:
            try:
                results['metadata'] = metadata_response.json()
            except:
                results['metadata'] = {'error': 'Could not parse metadata JSON'}
        
        # 3. Extract text
        logger.info("Analyzing document: extracting text...")
        text_response = requests.put(
            f'http://localhost:{TIKA_PORT}/tika',
            data=request.data,
            headers={'Accept': 'text/plain'},
            timeout=120
        )
        
        if text_response.status_code == 200:
            text = text_response.text
            results['text_preview'] = text[:1000] + ('...' if len(text) > 1000 else '')
            results['text_length'] = len(text)
            
            # Basic text analysis
            if text.strip():
                lines = text.split('\n')
                words = text.split()
                results['text_analysis'] = {
                    'lines': len(lines),
                    'words': len(words),
                    'characters': len(text),
                    'non_empty_lines': len([l for l in lines if l.strip()])
                }
                
                # Try language detection
                try:
                    lang_response = requests.put(
                        f'http://localhost:{TIKA_PORT}/language/stream',
                        data=text.encode('utf-8'),
                        headers={'Content-Type': 'text/plain'},
                        timeout=10
                    )
                    if lang_response.status_code == 200:
                        results['detected_language'] = lang_response.text.strip()
                except:
                    results['detected_language'] = 'Could not detect'
        
        # Summary
        processing_time = time.time() - start_time
        results['analysis_summary'] = {
            'success': True,
            'processing_time': round(processing_time, 3),
            'file_size': len(request.data),
            'components_analyzed': ['type_detection', 'metadata_extraction', 'text_extraction', 'language_detection']
        }
        
        logger.info(f"✅ Document analysis completed in {processing_time:.3f}s")
        return results
        
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}")
        abort(500, {'error': f'Analysis failed: {str(e)}'})

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': str(error.description)}), 401

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error.description)}), 400

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File Too Large', 'message': str(error.description)}), 413

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
    
    # Check Tika server status in background thread
    logger.info("🚀 Starting Secure Tika Server (Full Version)...")
    tika_thread = threading.Thread(target=check_tika_server, daemon=True)
    tika_thread.start()
    
    # Start Flask app
    logger.info(f"🌐 Starting Flask app on port {PORT}")
    logger.info("📋 Using official Apache Tika Docker image with full parser support")
    app.run(host='0.0.0.0', port=PORT, debug=False)
