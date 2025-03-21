from flask import Flask, request, Response, jsonify
import requests
import json
from flask_cors import CORS
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Allow all origins

OLLAMA_SERVER_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"

# Prompt template for text summarization
SUMMARY_PROMPT_TEMPLATE = """
You are an AI-powered text summarizer. Your goal is to generate a concise and coherent summary of the given input text while preserving its key points, main ideas, and essential details. The summary should:
- Properly structured and grammatically correct
- Retain the most critical information and eliminate redundant or less relevant details.
- Maintain logical flow and coherence, ensuring that the summary is easy to understand.
- Use clear, concise language while maintaining the original intent of the text.
- Avoid introducing new information or altering the meaning of the content.

Given the following input text, generate a summary:

Input Text:
{text}

Output Summary:
"""

# Prompt template for title generation
TITLE_PROMPT_TEMPLATE = """
You are an AI-powered title generator. Your goal is to generate a short, catchy, and informative title for the given input text. The title should:
- Be concise (2 to 5 words max).
- Warning ! You must not exceede the word limit .
- Capture the essence and key idea of the input text.
- Be engaging and relevant without unnecessary words.
- Avoid generic or vague titles.
- Not be misleading or introduce new information.

Given the following input text, generate a single-line title:

Input Text:
{text}

Output Title:
"""

@app.route("/summarize", methods=["POST"])
def summarize_text():
    try:
        req_data = request.get_json()
        if not req_data or "text" not in req_data:
            return jsonify({"error": "Missing 'text' field in request"}), 400
        
        text_to_summarize = req_data["text"]
        prompt = SUMMARY_PROMPT_TEMPLATE.format(text=text_to_summarize)
        
        ollama_payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True  # Enable streaming
        }
        
        response = requests.post(
            OLLAMA_SERVER_URL,
            json=ollama_payload,
            stream=True
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from Ollama"}), 500

        def generate():
            try:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            yield chunk.get("response", "")
                        except json.JSONDecodeError:
                            app.logger.error("Failed to decode JSON chunk")
                        except KeyError:
                            app.logger.error("Malformed response chunk")
            except Exception as e:
                app.logger.error(f"Stream error: {str(e)}")
            finally:
                response.close()

        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate_labels", methods=["POST"])
def generate_labels():
    try:
        req_data = request.get_json()
        if not req_data or "text" not in req_data:
            return jsonify({"error": "Missing 'text' field in request"}), 400

        issue_text = req_data["text"]

        # Strict prompt ensuring LLM returns only labels
        LABEL_PROMPT_TEMPLATE = """
        You are an AI-driven GitHub issue labeler responsible for assigning the 2-3 most relevant labels to a GitHub issue description.
        Only use labels from the predefined list below.
        Strict Rule For Response : **ONLY WRITE THE LABELS , NO EXPLANATION NEEDED IN FINAL RESPONSE AFTER THINKING PHASE , MAKE SURE TO FOLLOW THIS**
        ### Rules for Label Selection:
        1. Choose **only 2-3 labels maximum** that best describe the issue .
        2. Use **only** labels from the given list.
        3. If the issue is **critical**, include a **priority label** (`"priority: high"`, `"priority: medium"`, or `"priority: low"`).
        4. If the issue is related to a specific area (e.g., frontend, backend, database, CI/CD), assign the appropriate **category label**.
        5. If the issue lacks details, add `"needs more info"`.
        6. If unsure, default to `"triage"`.
        
        ### Available Labels:
        {labels}

        ### Example Issues and Correct Labels:

        **Example 1: Bug in Authentication System**
        _Issue:_ "Users are intermittently seeing 'Invalid Credentials' errors even when entering correct login details. This issue occurs randomly about 20% of the time in production."
        _Labels:_ `"bug"`, `"priority: high"`, `"backend"`

        **Example 2: Feature Request for Dark Mode**
        _Issue:_ "We should add a dark mode option for better accessibility. Many users have requested this."
        _Labels:_ `"feature"`, `"accessibility"`, `"frontend"`

        **Example 3: CI/CD Pipeline Failure**
        _Issue:_ "The CI/CD pipeline fails randomly when running integration tests. Deployment is blocked."
        _Labels:_ `"bug"`, `"CI/CD"`, `"blocked"`

        **Example 4: Performance Issue**
        _Issue:_ "The `/getUserHistory` API takes more than 5 seconds to respond. We need to optimize it to be under 1 second."
        _Labels:_ `"performance"`, `"backend"`, `"priority: medium"`

        ---
        **GitHub Issue to Label:**
        {text}

        **Selected Labels (2-3 only, comma-separated):**
        """

        GITHUB_LABELS = [
            "bug", "feature", "enhancement", "documentation", "refactor",
            "security", "performance", "accessibility", "priority: high",
            "priority: medium", "priority: low", "triage", "in progress",
            "blocked", "duplicate", "wontfix", "invalid", "needs more info",
            "ready for review", "frontend", "backend", "database", "CI/CD",
            "devops", "dependencies", "testing", "good first issue",
            "help wanted", "hard", "moderate", "breaking change", "patch",
            "minor update", "major update", "deprecated", "discussion",
            "question", "proposal"
        ]

        prompt = LABEL_PROMPT_TEMPLATE.format(
            labels=", ".join(GITHUB_LABELS),
            text=issue_text
        )

        ollama_payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True  # Enable streaming
        }

        response = requests.post(
            OLLAMA_SERVER_URL,
            json=ollama_payload,
            stream=True
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from Ollama"}), 500

        def generate():
            try:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            yield chunk.get("response", "")
                        except json.JSONDecodeError:
                            app.logger.error("Failed to decode JSON chunk")
                        except KeyError:
                            app.logger.error("Malformed response chunk")
            except Exception as e:
                app.logger.error(f"Stream error: {str(e)}")
            finally:
                response.close()

        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 
        

# Configure upload settings
UPLOAD_FOLDER = 'user_pdf'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created directory: {UPLOAD_FOLDER}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/pdf', methods=['POST'])
def upload_pdf():
    # Check if the request contains a file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # Check if file was actually selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if the file is a PDF
    if file and allowed_file(file.filename):
        # Secure the filename to prevent path traversal attacks
        filename = secure_filename(file.filename)
        
        # Ensure the upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        # Save the file to the upload folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath,
            'storage_directory': app.config['UPLOAD_FOLDER']
        }), 201
    else:
        return jsonify({'error': 'File type not allowed. Please upload a PDF file'}), 400



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
