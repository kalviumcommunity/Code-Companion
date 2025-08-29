# app.py

import os
import json
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

# We no longer import the official library's prompt object
# from prompts import CODE_COMPANION_SYSTEM_PROMPT

# Instead, we define the system prompt as a simple string here
CODE_COMPANION_SYSTEM_PROMPT = """
You are "Code Companion," an expert AI programmer and software architect.
Your primary purpose is to help users by generating high-quality, efficient, and secure code snippets in response to their requests. You must also provide a clear, concise explanation of how the code works and list any dependencies required to run it.
"""

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
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
    
    # The URL for the Gemini 1.5 Flash model API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # The data payload for the API request
    payload = {
        "systemInstruction": {
            "parts": {"text": CODE_COMPANION_SYSTEM_PROMPT}
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }]
    }
    
    # The headers for the request
    headers = {'Content-Type': 'application/json'}

    try:
        # Make the POST request to the API
        api_response = requests.post(url, headers=headers, data=json.dumps(payload))
        api_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        # Parse the JSON response
        response_data = api_response.json()
        
        # Extract the generated text
        generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Format for HTML and return to the user
        formatted_response = generated_text.replace('\n', '<br>')
        return f"<h1>AI Response:</h1><div>{formatted_response}</div>"

    except requests.exceptions.RequestException as e:
        # Handle network errors
        print(f"A network error occurred: {e}")
        return f"<h1>A Network Error Occurred</h1><p>Could not connect to the API. Details: {e}</p>", 500
    except (KeyError, IndexError) as e:
        # Handle errors in parsing the response from the API
        print(f"Error parsing API response: {e}")
        print(f"Full response: {api_response.text}") # Log the full response for debugging
        return "<h1>Error</h1><p>Could not parse the response from the API.</p>", 500
    except Exception as e:
        # Handle all other errors
        print(f"An unexpected error occurred: {e}")
        return f"<h1>An Unexpected Error Occurred</h1><p>Details: {e}</p>", 500

if __name__ == '__main__':
    app.run(debug=True)