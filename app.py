from flask import Flask, request, Response, jsonify
import requests
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins

OLLAMA_SERVER_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"

# Prompt template for text summarization
SUMMARY_PROMPT_TEMPLATE = """
You are an AI-powered text summarizer. Your goal is to generate a concise and coherent summary of the given input text while preserving its key points, main ideas, and essential details. The summary should:
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

@app.route("/generate_title", methods=["POST"])
def generate_title():
    try:
        req_data = request.get_json()
        if not req_data or "text" not in req_data:
            return jsonify({"error": "Missing 'text' field in request"}), 400
        
        text_to_title = req_data["text"]
        prompt = TITLE_PROMPT_TEMPLATE.format(text=text_to_title)
        
        ollama_payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False  # No need for streaming for a short response
        }
        
        response = requests.post(
            OLLAMA_SERVER_URL,
            json=ollama_payload
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from Ollama"}), 500
        
        response_data = response.json()
        title = response_data.get("response", "")
        
        return jsonify({"title": title})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
