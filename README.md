# AkiyaVision (アキヤビジョン)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fmtfum%2Fakiya-vision&env=REPLICATE_API_TOKEN&envDescription=API%20token%20for%20Replicate%20AI%20service&envLink=https%3A%2F%2Freplicate.com%2Faccount%2Fapi-tokens)

AI-powered web application for visualizing renovated vacant houses (空き家) in Japan using Stable Diffusion image generation.

## Features

- Browse sample vacant houses from Tokyo (東京都)
- Select from pre-loaded demo images of various room types
- Generate renovation visualizations in 12 styles:
  - Modern (モダン) - 現代的なデザイン
  - Japanese Modern (和モダン) - 日本の伝統×現代
  - Western (洋風) - 西洋スタイル
  - Scandinavian (北欧風) - シンプル&ナチュラル
  - Industrial (インダストリアル) - 工業的デザイン
  - Minimalist Zen (ミニマリスト禅) - 静寂と調和
  - Showa Retro (昭和レトロ) - 懐かしい昭和時代
  - Luxury (ラグジュアリー) - 高級ホテル風
  - Eco Natural (エコナチュラル) - 環境に優しい
  - Mediterranean (地中海風) - 南欧リゾート
  - Smart Home (スマートホーム) - 未来型住宅
  - Bohemian (ボヘミアン) - 自由で芸術的
- Interactive before/after comparison slider
- Inquiry form for interested customers
- Responsive design with mobile navigation menu

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd akiya-vision
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Replicate API:
```bash
cp .env.template .env
# Edit .env and add your REPLICATE_API_TOKEN
```

Get your API token from: https://replicate.com/account/api-tokens

5. Run the application:
```bash
# Recommended: Use uvicorn directly to avoid warnings and enable auto-reload
uvicorn app:app --reload

# Alternative: Run with python (no auto-reload)
python app.py
```

6. Open http://localhost:8000 in your browser

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app
```

## Project Structure

```
akiya-vision/
├── app.py              # FastAPI backend
├── requirements.txt    # Python dependencies
├── .env               # API keys (create from .env.template)
├── static/
│   ├── script.js      # Frontend JavaScript
│   ├── favicon.svg    # Site favicon
│   └── demo-images/   # Pre-loaded demo images
│       ├── demo1.jpg  # 台所 (Kitchen)
│       ├── demo2.jpg  # 外観 (Exterior)
│       ├── demo3.jpeg # 廊下 (Corridor)
│       ├── demo4.jpeg # 和室 (Japanese room)
│       ├── demo5.jpg  # 空き部屋 (Empty room)
│       └── demo6.jpg  # リビング (Living room)
├── templates/
│   └── index.html     # Main UI template
└── tests/             # Test suite
```

## Technologies

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + Vanilla JavaScript
- **Styling**: Tailwind CSS (CDN)
- **AI**: Replicate API - Interior AI model by erayyavuz
- **Testing**: pytest + Playwright MCP

## Performance

- Image generation: ~$0.002 per image
- Generation time: 1+ minutes per image
- Specialized interior design AI model for better renovation results

## Deployment

### Deploy to Vercel

1. Click the "Deploy with Vercel" button at the top of this README
2. Create a new repository or connect to an existing one
3. Add your `REPLICATE_API_TOKEN` environment variable
4. Deploy!

### Manual Deployment

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy to Vercel:
```bash
vercel
```

3. Set environment variables in Vercel dashboard:
   - Go to Settings → Environment Variables
   - Add `REPLICATE_API_TOKEN` with your Replicate API token

4. Deploy to production:
```bash
vercel --prod
```

### Automatic Deployment with GitHub Actions

To enable automatic deployment when pushing to main branch:

1. **Connect your GitHub repository to Vercel:**
   ```bash
   vercel link
   ```

2. **Get your Vercel credentials:**
   - Go to [Vercel Account Settings](https://vercel.com/account/tokens)
   - Create a new token and save it
   - Go to your project's Settings → General
   - Copy your Org ID and Project ID

3. **Add GitHub Secrets:**
   Go to your GitHub repository → Settings → Secrets and variables → Actions, then add:
   - `VERCEL_TOKEN`: Your Vercel access token
   - `VERCEL_ORG_ID`: Your Vercel organization ID
   - `VERCEL_PROJECT_ID`: Your Vercel project ID

4. **Push to main branch:**
   ```bash
   git add .
   git commit -m "Enable automatic deployment"
   git push origin main
   ```

Now your app will automatically deploy to Vercel when you:
- Push to `main` branch → Production deployment
- Create a pull request → Preview deployment with comment