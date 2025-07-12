# AkiyaVision (アキヤビジョン)

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