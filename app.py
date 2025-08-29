# app.py

import os
import json
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

CODE_COMPANION_SYSTEM_PROMPT = """
You are "Code Companion," an expert AI programmer and software architect.
Your primary purpose is to help users by generating high-quality, efficient, and secure code snippets in response to their requests. You must also provide a clear, concise explanation of how the code works and list any dependencies required to run it.
"""

load_dotenv()
app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handles the code generation request by making a direct API call."""
    api_key = os.getenv("GOOGLE_API_KEY")
    user_prompt = request.form['user_prompt']
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "systemInstruction": {
            "parts": {"text": CODE_COMPANION_SYSTEM_PROMPT}
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}

    try:
        api_response = requests.post(url, headers=headers, data=json.dumps(payload))
        api_response.raise_for_status()
        
        response_data = api_response.json()
        
        # --- NEW CODE FOR TOPIC 3 ---
        # Extract token usage from the response metadata
        usage_metadata = response_data.get('usageMetadata', {})
        total_tokens = usage_metadata.get('totalTokenCount', 'N/A')
        print(f"Total tokens used: {total_tokens}")
        # --- END OF NEW CODE ---
        
        generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        formatted_response = generated_text.replace('\n', '<br>')
        return f"<h1>AI Response:</h1><div>{formatted_response}</div>"

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
        return f"<h1>A Network Error Occurred</h1><p>Could not connect to the API. Details: {e}</p>", 500
    except (KeyError, IndexError) as e:
        print(f"Error parsing API response: {e}")
        print(f"Full response: {api_response.text}")
        return "<h1>Error</h1><p>Could not parse the response from the API.</p>", 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"<h1>An Unexpected Error Occurred</h1><p>Details: {e}</p>", 500

if __name__ == '__main__':
    app.run(debug=True)