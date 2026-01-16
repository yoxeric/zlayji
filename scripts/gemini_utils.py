import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment.")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_image(image_path):
    """Analyze image to check if it's a suitable high-quality wallpaper."""
    try:
        img = Image.open(image_path)
        prompt = "Is this image a high-quality aesthetic wallpaper? Respond with 'YES' or 'NO' and a short reason."
        
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return "ERROR"

def generate_social_content(image_path, category):
    """Generate captions and hashtags for different social platforms."""
    try:
        img = Image.open(image_path)
        prompt = f"""
        Generate engaging captions and hashtags for this {category} wallpaper for:
        1. Instagram/TikTok (short, catchy, emoji-rich)
        2. X (Twitter) (concise, viral style)
        3. Pinterest (descriptive, SEO-friendly)
        
        Output in JSON format with keys: 'instagram', 'x', 'pinterest'.
        """
        
        response = model.generate_content([prompt, img])
        # Clean response text as it might contain markdown JSON blocks
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        return text
    except Exception as e:
        print(f"Error generating content: {e}")
        return "{}"

if __name__ == "__main__":
    # Test block
    # print(analyze_image("test.jpg"))
    pass
