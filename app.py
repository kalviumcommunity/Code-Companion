# app.py

import os
import json
import requests
import ast
from flask import Flask, render_template, request
from dotenv import load_dotenv

# Final System Prompt combining all instructions
CODE_COMPANION_SYSTEM_PROMPT = """
You are "Code Companion," an expert AI programmer.
Your purpose is to help users by generating code snippets and using available tools if requested.

When generating code without a function call, you must respond in a specific JSON format. The JSON object must have three keys:
1.  "code": A string containing the complete, runnable code snippet.
2.  "explanation": A string explaining the code in a clear, concise way.
3.  "dependencies": A string listing any required libraries or dependencies. If there are none, it should say "None".

Do not include any text outside of the JSON object.
"""

load_dotenv()
app = Flask(__name__)

# Function for the 'validate_python_code' tool
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

# Tool definition for the AI
tools = [{"function_declarations": [{"name": "validate_python_code","description": "Validates a string of Python code to check for syntax errors.","parameters": {"type": "OBJECT","properties": {"code_string": {"type": "STRING","description": "The Python code snippet to validate."}},"required": ["code_string"]}}]}]

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handles the code generation request, incorporating all concepts."""
    api_key = os.getenv("GOOGLE_API_KEY")
    user_prompt = request.form['user_prompt']
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Payload with all features we've implemented
    payload = {
        "systemInstruction": {"parts": [{"text": CODE_COMPANION_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "tools": tools,
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "topK": 40,
            "stopSequences": ["---"],
            "response_mime_type": "application/json"
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    final_html_response = ""

    try:
        # First API Call
        api_response = requests.post(url, headers=headers, data=json.dumps(payload))
        api_response.raise_for_status()
        response_data = api_response.json()

        # Log token usage
        usage_metadata = response_data.get('usageMetadata', {})
        total_tokens = usage_metadata.get('totalTokenCount', 'N/A')
        print(f"Total tokens used (first call): {total_tokens}")

        candidate = response_data['candidates'][0]
        first_part = candidate['content']['parts'][0]

        # Handle Function Calling
        if 'functionCall' in first_part:
            function_call = first_part['functionCall']
            args = function_call.get('args', {})
            code_to_validate = args.get('code_string', "")

            tool_result = validate_python_code(code_to_validate)
            print(f"Validation Result: {tool_result}")

            payload["contents"].append(candidate['content'])
            payload["contents"].append({
                "role": "tool",
                "parts": [{"functionResponse": {"name": function_call['name'], "response": json.loads(tool_result)}}]
            })

            # Second API call
            second_response = requests.post(url, headers=headers, data=json.dumps(payload))
            second_response.raise_for_status()
            second_response_data = second_response.json()
            
            final_text = second_response_data['candidates'][0]['content']['parts'][0]['text']
            # Format as simple HTML for the template
            final_html_response = f"<div>{final_text.replace(chr(10), '<br>')}</div>"

        # Handle Structured Output
        else:
            generated_text = first_part.get('text', '{}').split("---")[0]
            parsed_json = json.loads(generated_text)
            
            code = parsed_json.get('code', 'Error: Code not found.')
            explanation = parsed_json.get('explanation', 'Error: Explanation not found.')
            dependencies = parsed_json.get('dependencies', 'Error: Dependencies not found.')

            # Format the data into a clean HTML block for the template
            final_html_response = f"""
            <h3>Generated Code</h3>
            <pre><code>{code.replace('<', '&lt;').replace('>', '&gt;')}</code></pre>
            <h3>Explanation</h3>
            <p>{explanation.replace(chr(10), '<br>')}</p>
            <h3>Dependencies</h3>
            <p>{dependencies}</p>
            """
        
        # Re-render the same page, passing the AI response to the template
        return render_template('index.html', ai_response=final_html_response)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        error_message = f"<h2>An Unexpected Error Occurred</h2><p>Details: {e}</p>"
        # Re-render the page with the error message
        return render_template('index.html', ai_response=error_message)

if __name__ == '__main__':
    app.run(debug=True)

