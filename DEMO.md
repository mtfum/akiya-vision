# AkiyaVision Demo Instructions

## Prerequisites

1. Ensure you have a Replicate API token (optional - app works with mock data)
   - Get one at: https://replicate.com/account/api-tokens
   - Add to `.env` file: `REPLICATE_API_TOKEN=your_token_here`

2. Activate virtual environment and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo

1. Start the server:
```bash
python app.py
```

2. Open your browser to: http://localhost:8000

## Demo Flow

### Step 1: Select a Property
- Two sample properties from Eiheiji-cho are displayed
- Click on either property card to select it
- Property details will appear below

### Step 2: Upload an Image
- Click "画像を選択" button
- Select any image of a room or building interior
- Image preview will appear after upload

### Step 3: Choose Renovation Style
Four styles are available:
- **モダン (Modern)** 🏢 - Clean, minimalist design
- **和モダン (Japanese Modern)** 🏯 - Traditional meets contemporary
- **洋風 (Western)** 🏡 - Western-style interiors
- **北欧風 (Scandinavian)** 🌲 - Nordic simplicity

### Step 4: View Results
- AI generation takes ~10 seconds (or instant with mock data)
- Interactive before/after slider appears
- Drag the slider or click to compare
- Try different styles on the same image

## Key Features to Demonstrate

1. **Responsive Design**
   - Works on mobile and desktop
   - Touch-friendly slider interface

2. **Japanese Language Support**
   - Full Japanese UI
   - Property information in Japanese

3. **Fast Performance**
   - Optimized image generation (512x512)
   - In-memory storage for demo

4. **Error Handling**
   - Try uploading non-image files
   - Upload without selecting a house

## Testing Without API Key

The app works without a Replicate API key:
- Returns the original image as mock result
- Instant response time
- Perfect for UI/UX testing

## Troubleshooting

1. **Port already in use**
   ```bash
   # Kill existing process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Module not found errors**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Static files not loading**
   - Check that `/static` and `/templates` directories exist
   - Verify `script.js` and `index.html` are present

## Performance Notes

- First load may take longer (Tailwind CSS CDN)
- Image uploads are base64 encoded (larger payload)
- Mock mode recommended for demos without internet

## Demo Tips

1. Prepare sample interior photos beforehand
2. Test all 4 styles to show variety
3. Emphasize the before/after slider interaction
4. Mention future possibilities (3D, VR, batch processing)