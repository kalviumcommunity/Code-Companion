# app.py

import os
import json
import requests
import ast
from flask import Flask, render_template, request
from dotenv import load_dotenv

CODE_COMPANION_SYSTEM_PROMPT = """
You are "Code Companion," an expert AI programmer.
Your purpose is to help users by generating code snippets and using available tools if requested.
"""

load_dotenv()
app = Flask(__name__)

def validate_python_code(code_string: str):
    """Validates a string of Python code for syntax errors."""
    try:
        if code_string.strip().startswith("```python"):
            code_string = code_string.strip()[9:-3].strip()
        elif code_string.strip().startswith("```"):
             code_string = code_string.strip()[3:-3].strip()
        
        ast.parse(code_string)
        return json.dumps({"status": "success", "message": "Code syntax is valid."})
    except SyntaxError as e:
        return json.dumps({"status": "error", "message": f"Syntax error: {e}"})

tools = [{"function_declarations": [{"name": "validate_python_code","description": "Validates a string of Python code to check for syntax errors.","parameters": {"type": "OBJECT","properties": {"code_string": {"type": "STRING","description": "The Python code snippet to validate."}},"required": ["code_string"]}}]}]

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handles the code generation request, including function calls."""
    api_key = os.getenv("GOOGLE_API_KEY")
    user_prompt = request.form['user_prompt']
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # --- THIS BLOCK IS NOW CORRECTED ---
    payload = {
        "systemInstruction": {"parts": [{"text": CODE_COMPANION_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}], # Added "role": "user"
        "tools": tools,
        "generationConfig": {"temperature": 0.3}
    }
    # --- END OF CORRECTION ---
    
    headers = {'Content-Type': 'application/json'}

    try:
        # First API Call
        api_response = requests.post(url, headers=headers, data=json.dumps(payload))
        api_response.raise_for_status()
        response_data = api_response.json()

        candidate = response_data['candidates'][0]
        first_part = candidate['content']['parts'][0]

        if 'functionCall' in first_part:
            function_call = first_part['functionCall']
            args = function_call.get('args', {})
            code_to_validate = args.get('code_string', "")

            tool_result = validate_python_code(code_to_validate)
            print(f"Validation Result: {tool_result}")

            payload["contents"].append(candidate['content'])
            
            payload["contents"].append({
                "role": "tool",
                "parts": [{"functionResponse": {"name": function_call['name'],"response": json.loads(tool_result)}}]
            })

            # Second API call
            second_response = requests.post(url, headers=headers, data=json.dumps(payload))
            second_response.raise_for_status()
            second_response_data = second_response.json()
            final_text = second_response_data['candidates'][0]['content']['parts'][0]['text']
        else:
            final_text = first_part.get('text', 'No text content found.')

        formatted_response = final_text.replace('\n', '<br>')
        return f"<h1>AI Response:</h1><div>{formatted_response}</div>"

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        try: print(f"Response content: {api_response.text}")
        except NameError: pass
        return f"<h1>An Unexpected Error Occurred</h1><p>Details: {e}</p>", 500

if __name__ == '__main__':
    app.run(debug=True)