# Secure Tika Server (Latest Version)

A production-ready Apache Tika server with API key authentication, automatic latest version fetching, and comprehensive document processing capabilities.

## 🚀 Features

- 🔐 **API key authentication** - Secure access control
- 📄 **1000+ document formats** - PDF, Word, Excel, PowerPoint, images, and more
- 🔄 **Latest Tika version** - Automatically downloads newest version on deployment
- 🖼️ **OCR capabilities** - Extract text from images and scanned documents
- 🌍 **Language detection** - Identify document languages
- 📊 **Metadata extraction** - Get detailed file information
- 🚀 **Serverless deployment** - Auto-scaling with pay-per-use pricing
- 📈 **Health monitoring** - Built-in status and logging
- 🌐 **Global CDN** - Fast response times worldwide

## 📡 API Endpoints

### Authentication
All requests require an API key in the header:
```bash
X-API-Key: your-secret-api-key
```

### Document Parsing
```bash
# Extract plain text (default)
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/pdf" \
  --data-binary @document.pdf \
  https://your-app.railway.app/parse

# Extract HTML with formatting
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  --data-binary @document.pdf \
  "https://your-app.railway.app/parse?format=html"

# Extract metadata only
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  --data-binary @document.pdf \
  "https://your-app.railway.app/parse?format=metadata"
```

### Document Analysis
```bash
# Detect document type
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  --data-binary @document.pdf \
  https://your-app.railway.app/detect

# Detect document language
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  --data-binary @document.pdf \
  https://your-app.railway.app/language
```

### Service Information
```bash
# Check service health
curl https://your-app.railway.app/health

# Get Tika version info
curl https://your-app.railway.app/version

# List supported file types (requires API key)
curl -H "X-API-Key: your-secret-api-key" \
  https://your-app.railway.app/types

# Service overview
curl https://your-app.railway.app/
```

## 🔧 Supported File Types

- **Documents:** PDF, Word (.doc, .docx), Excel (.xls, .xlsx), PowerPoint (.ppt, .pptx)
- **Text:** RTF, HTML, XML, CSV, TXT, Markdown
- **Images:** JPEG, PNG, GIF, TIFF, BMP (with OCR)
- **Archives:** ZIP, RAR, 7z, TAR
- **Audio/Video:** MP3, MP4, AVI (metadata extraction)
- **Scientific:** DICOM, NetCDF, HDF
- **CAD:** DWG, DXF
- **And 1000+ more formats**

## 🛡️ Security Features

- ✅ **API key authentication** - Only authorized access
- ✅ **HTTPS encryption** - Secure data transmission
- ✅ **No file storage** - Documents processed in memory only
- ✅ **Request logging** - Monitor access patterns
- ✅ **Input validation** - Prevent malicious uploads
- ✅ **Non-root execution** - Container security

## 💰 Cost Structure

### Railway Pricing (Pay-per-use)
- **Hobby Plan:** $5/month + usage
- **Pro Plan:** $20/month + usage
- **Only charged when processing documents**
- **Automatic sleep when idle**

### Usage Estimates
- **Light usage (100 docs/month):** $5-8/month
- **Medium usage (1000 docs/month):** $10-20/month
- **Heavy usage (10,000 docs/month):** $25-50/month

**Compare to always-on server:** $240+/month

## 🔄 Version Management

- ✅ **Latest version on deployment** - Always gets newest Tika
- ✅ **Stable during operation** - Version doesn't change mid-service
- ✅ **No manual updates needed** - Fully automatic
- ✅ **Version tracking** - Check `/version` endpoint

## 📊 Monitoring

### Health Checks
- **Endpoint:** `GET /health`
- **Status codes:** 200 (healthy), 503 (starting)
- **Includes:** Tika readiness, uptime, timestamp

### Logging
- **Railway Dashboard:** Real-time logs
- **Request tracking:** All API calls logged
- **Error monitoring:** Detailed error information
- **Performance metrics:** Processing times tracked

## 🚀 Deployment

This service auto-deploys from GitHub via Railway:
1. Push changes to main branch
2. GitHub Actions triggers
3. Railway builds latest container
4. Downloads newest Tika version
5. Service starts with updated code

## 🛠️ Development

### Local Testing
```bash
# Clone repository
git clone https://github.com/yourusername/secure-tika-server.git
cd secure-tika-server

# Set environment variables
export TIKA_SECRET=your-test-key
export PORT=8080

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### Environment Variables
- `TIKA_SECRET` - API key for authentication (required)
- `PORT` - Server port (default: 8080)

## 💻 Usage Examples

### JavaScript/TypeScript
```javascript
class TikaClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    async extractText(file, format = 'text') {
        const url = `${this.baseUrl}/parse?format=${format}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/octet-stream'
            },
            body: file
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(`HTTP ${response.status}: ${error.message}`);
        }
        
        return await response.json();
    }

    async detectType(file) {
        const response = await fetch(`${this.baseUrl}/detect`, {
            method: 'POST',
            headers: { 'X-API-Key': this.apiKey },
            body: file
        });
        
        return await response.json();
    }
}

// Usage
const tika = new TikaClient(
    'https://your-app.railway.app',
    'your-secret-api-key'
);

document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        try {
            const result = await tika.extractText(file);
            console.log('Extracted text:', result.content);
        } catch (error) {
            console.error('Error:', error.message);
        }
    }
});
```

### Python
```python
import requests
from typing import Dict, Any

class TikaClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'X-API-Key': api_key})

    def extract_text(self, file_path: str, format: str = 'text') -> Dict[str, Any]:
        """Extract text from a document file"""
        url = f"{self.base_url}/parse"
        params = {'format': format} if format != 'text' else {}
        
        with open(file_path, 'rb') as file:
            response = self.session.post(
                url, 
                params=params,
                data=file.read(),
                timeout=120
            )
        
        response.raise_for_status()
        return response.json()

    def detect_type(self, file_path: str) -> Dict[str, Any]:
        """Detect document MIME type"""
        with open(file_path, 'rb') as file:
            response = self.session.post(
                f"{self.base_url}/detect", 
                data=file.read()
            )
        
        response.raise_for_status()
        return response.json()

# Usage
tika = TikaClient(
    base_url='https://your-app.railway.app',
    api_key='your-secret-api-key'
)

try:
    result = tika.extract_text('document.pdf')
    print(f"Extracted {result['content_length']} characters")
    print(f"Text: {result['content'][:200]}...")
    
    doc_type = tika.detect_type('document.pdf')
    print(f"Document type: {doc_type['mime_type']}")
    
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

### Node.js
```javascript
const fetch = require('node-fetch');
const fs = require('fs');

class TikaClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }

    async extractText(filePath, format = 'text') {
        const url = `${this.baseUrl}/parse${format !== 'text' ? `?format=${format}` : ''}`;
        const fileBuffer = fs.readFileSync(filePath);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/octet-stream'
            },
            body: fileBuffer
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(`HTTP ${response.status}: ${error.message}`);
        }
        
        return await response.json();
    }
}

// Usage
async function main() {
    const tika = new TikaClient(
        'https://your-app.railway.app',
        'your-secret-api-key'
    );

    try {
        const result = await tika.extractText('test.pdf');
        console.log(`Extracted ${result.content_length} characters`);
        console.log('Text preview:', result.content.substring(0, 200));
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

## 🔍 Troubleshooting

### Common Issues

**Service starting (503 errors):**
- Tika server takes 30-60 seconds to initialize
- Check `/health` endpoint for readiness status
- Large documents may need more time

**Authentication errors (401):**
- Verify API key in Railway environment variables
- Check header format: `X-API-Key: your-key`
- Ensure no extra spaces in key value

**Processing timeouts:**
- Large files (>50MB) may timeout
- Try smaller files or increase timeout settings
- Check Railway logs for specific errors

**Build failures:**
- Verify all files are committed to GitHub
- Check GitHub Actions logs for details
- Ensure Dockerfile syntax is correct

### Performance Optimization

**For faster processing:**
- Use appropriate file formats (PDF vs images)
- Compress large files before processing
- Use metadata extraction for file analysis only
- Batch similar documents together

**For cost optimization:**
- Monitor usage in Railway dashboard
- Use Hobby plan for light usage
- Upgrade to Pro plan only when needed
- Process files during off-peak hours

### Getting Help

1. **Check Railway logs** for detailed error messages
2. **Test health endpoint** to verify service status
3. **Review GitHub Actions** for deployment issues
4. **Railway Discord:** https://discord.gg/railway
5. **Apache Tika docs:** https://tika.apache.org/

## 📈 Advanced Features

### Batch Processing
Process multiple files in one request:
```python
def process_batch(file_paths):
    results = []
    for file_path in file_paths:
        try:
            result = tika.extract_text(file_path)
            results.append({
                'file': file_path,
                'success': True,
                'content': result['content']
            })
        except Exception as e:
            results.append({
                'file': file_path,
                'success': False,
                'error': str(e)
            })
    return results
```

### Custom Metadata Extraction
Extract specific metadata fields:
```python
def get_document_info(file_path):
    metadata = tika.extract_text(file_path, format='metadata')
    return {
        'author': metadata['metadata'].get('Author', 'Unknown'),
        'created': metadata['metadata'].get('Creation-Date', 'Unknown'),
        'pages': metadata['metadata'].get('xmpTPg:NPages', 'Unknown'),
        'title': metadata['metadata'].get('title', 'Unknown')
    }
```

### Error Handling and Retries
Implement robust error handling:
```python
import time
from typing import Optional

def extract_with_retry(file_path: str, max_retries: int = 3) -> Optional[Dict]:
    for attempt in range(max_retries):
        try:
            return tika.extract_text(file_path)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            raise
    return None
```

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 🔗 Links

- **Railway:** https://railway.app
- **Apache Tika:** https://tika.apache.org/
- **GitHub Repository:** https://github.com/yourusername/secure-tika-server
- **Support:** Create an issue in the GitHub repository

---

**Built with ❤️ using Apache Tika, Python Flask, and Railway**
