"""
Test Gemini API models to find which ones work
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

# Test different model names
model_names = [
    'gemini-3-flash',
    'gemini-2.5-flash', 
    'gemini-flash-latest',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
]

print("🧪 Testing Gemini API Models\n")
print("=" * 60)

working_models = []

for model_name in model_names:
    try:
        print(f"\n📝 Testing: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'hello' in one word")
        print(f"✅ {model_name} - WORKS")
        print(f"   Response: {response.text.strip()}")
        working_models.append(model_name)
    except Exception as e:
        print(f"❌ {model_name} - FAILED")
        error_msg = str(e)
        if '404' in error_msg:
            print(f"   Error: Model not found (404)")
        else:
            print(f"   Error: {error_msg[:100]}")

print("\n" + "=" * 60)
print(f"\n✅ Working models: {len(working_models)}/{len(model_names)}")

if working_models:
    print(f"\n🎯 Recommended model: {working_models[0]}")
    print(f"\nUpdate .env with:")
    print(f"AI_MODEL={working_models[0]}")
else:
    print("\n❌ No working models found. Check your API key.")
