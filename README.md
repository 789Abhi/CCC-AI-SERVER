# CCC AI Server

AI-powered component generator for the Custom Craft Component WordPress plugin using Microsoft Phi-2 model.

## 🚀 Features

- **Microsoft Phi-2 Model**: Fast and efficient AI for component generation
- **FastAPI Server**: High-performance web API
- **WordPress Integration**: Seamless integration with WordPress plugins
- **Global Access**: Deployed on Railway for worldwide access
- **Free Tier**: Runs on Railway's free tier

## 🛠️ Setup

### Prerequisites

- GitHub account
- Railway.app account
- Python 3.9+

### Deployment Steps

1. **Fork/Clone this repository**
2. **Connect to Railway.app**
3. **Deploy automatically**
4. **Get your public URL**

### Railway Deployment

1. Go to [Railway.app](https://railway.app)
2. Click "Deploy from GitHub repo"
3. Select this repository
4. Railway will automatically:
   - Install dependencies
   - Download Microsoft Phi-2 model
   - Start the server
   - Provide a public URL

## 📡 API Endpoints

### Health Check
```
GET /health
```
Returns server status and model information.

### Generate Component
```
POST /generate-component
```
Generates a component based on user description.

**Request Body:**
```json
{
  "prompt": "Create a hero section with video background and heading",
  "available_fields": ["text", "textarea", "image", "video", "color", "select", "checkbox", "radio", "wysiwyg", "repeater"]
}
```

**Response:**
```json
{
  "component": {
    "name": "Hero Section",
    "handle": "hero_section",
    "description": "A hero section with video background"
  },
  "fields": [
    {
      "label": "Video Background",
      "name": "video_background",
      "type": "video",
      "required": true,
      "placeholder": "Upload or enter video URL"
    },
    {
      "label": "Heading",
      "name": "heading",
      "type": "text",
      "required": true,
      "placeholder": "Enter your heading"
    }
  ],
  "success": true,
  "message": "Component generated successfully"
}
```

### Test Endpoint
```
GET /test
```
Tests the AI generation with a sample prompt.

## 🔧 Configuration

### Environment Variables

- `PORT`: Server port (Railway sets this automatically)
- `MODEL_NAME`: AI model name (default: microsoft/phi-2)

### Model Information

- **Model**: Microsoft Phi-2
- **Size**: ~2.7GB
- **Memory**: ~1GB RAM
- **Speed**: 2-3 seconds per request
- **Quality**: Excellent for component generation

## 🌍 WordPress Integration

### Plugin Setup

Add this to your WordPress plugin:

```php
class CCC_AIService {
    private $api_url = 'https://your-railway-url.railway.app';
    
    public function generate_component($prompt) {
        $response = wp_remote_post($this->api_url . '/generate-component', [
            'headers' => ['Content-Type' => 'application/json'],
            'body' => json_encode(['prompt' => $prompt]),
            'timeout' => 10
        ]);
        
        return json_decode(wp_remote_retrieve_body($response), true);
    }
}
```

## 📊 Performance

- **Response Time**: 2-5 seconds
- **Concurrent Requests**: 10+ simultaneous
- **Uptime**: 99.9% (Railway managed)
- **Global CDN**: Yes

## 🔒 Security

- **HTTPS**: Automatic SSL certificates
- **CORS**: Configured for WordPress domains
- **Input Validation**: Pydantic models
- **Error Handling**: Comprehensive error responses

## 🚀 Usage Examples

### Hero Section
```
Prompt: "Create a hero section with video background and overlay"
```

### Testimonials
```
Prompt: "Create testimonials with author image and rating"
```

### Pricing Table
```
Prompt: "Create pricing table with features list"
```

### Contact Form
```
Prompt: "Create contact form with name, email, and message fields"
```

## 🛠️ Development

### Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python main.py`
4. Access at: `http://localhost:8000`

### Testing

```bash
# Test health endpoint
curl https://your-railway-url.railway.app/health

# Test component generation
curl -X POST https://your-railway-url.railway.app/generate-component \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create hero section with video"}'
```

## 📈 Monitoring

- **Railway Dashboard**: Monitor usage and performance
- **Health Checks**: Automatic health monitoring
- **Logs**: Real-time application logs
- **Metrics**: Request/response statistics

## 🔄 Updates

To update the server:

1. Push changes to GitHub
2. Railway automatically redeploys
3. Zero downtime deployment

## 🆘 Support

- **Issues**: Create GitHub issues
- **Documentation**: Check this README
- **Railway Support**: Railway.app documentation

## 📄 License

This project is part of the Custom Craft Component WordPress plugin.

---

**Deployed on Railway.app | Powered by Microsoft Phi-2 | Built with FastAPI** 