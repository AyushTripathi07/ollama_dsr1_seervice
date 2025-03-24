from flask import Flask, request, Response, jsonify
import requests
import json
from flask_cors import CORS
import re
import os
from werkzeug.utils import secure_filename
from controller import extract_text_and_images
from threading import Thread
import time
import base64

app = Flask(__name__)
CORS(app)  # Allow all origins

OLLAMA_SERVER_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:7b"

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


# Constants for LLM endpoints
GEMMA_SERVER_URL = "http://localhost:11434/api/generate"  # Adjust if different
DEEPSEEK_SERVER_URL = "http://localhost:11434/api/generate"  # Adjust if different
GEMMA_MODEL_NAME = "gemma3:4b"  # Replace with actual model name
DEEPSEEK_MODEL_NAME = "deepseek-r1:7b"  # From your original code

# Define processing status constants
STATUS_PENDING = "pending"
STATUS_PROCESSING_IMAGES = "processing_images"
STATUS_PROCESSING_TEXT = "processing_text"
STATUS_GENERATING_SUMMARY = "generating_summary"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# In-memory storage for processing status (replace with database in production)
processing_jobs = {}

def process_pdf_in_background(pdf_path, filename, job_id):
    """Background processing function for PDF analysis"""
    try:
        # Update status
        processing_jobs[job_id] = {
            "status": STATUS_PROCESSING_TEXT,
            "filename": filename,
            "created_at": time.time()
        }
        
        # Create a directory for extracted content
        extraction_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_extracted")
        if not os.path.exists(extraction_dir):
            os.makedirs(extraction_dir)
        
        # Extract text and images from the PDF
        text_content, image_paths = extract_text_and_images(pdf_path, extraction_dir)
        
        # Save extracted text to a file
        text_file_path = os.path.join(extraction_dir, "extracted_text.txt")
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        # Process images with Gemma
        processing_jobs[job_id]["status"] = STATUS_PROCESSING_IMAGES
        image_analysis = process_images_with_gemma(image_paths)
        
        # Save image analysis to a file
        image_analysis_path = os.path.join(extraction_dir, "image_analysis.txt")
        with open(image_analysis_path, "w", encoding="utf-8") as f:
            f.write(image_analysis)
        
        # Generate final summary with Deepseek
        processing_jobs[job_id]["status"] = STATUS_GENERATING_SUMMARY
        final_summary = generate_summary_with_deepseek(text_content, image_analysis)
        
        # Save final summary
        summary_path = os.path.join(extraction_dir, "final_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(final_summary)
        
        # Update job status to completed
        processing_jobs[job_id]["status"] = STATUS_COMPLETED
        processing_jobs[job_id]["summary_path"] = summary_path
        processing_jobs[job_id]["completed_at"] = time.time()
        
        print(f"Completed processing PDF {filename}")
        
    except Exception as e:
        print(f"Error processing PDF {filename}: {str(e)}")
        processing_jobs[job_id]["status"] = STATUS_FAILED
        processing_jobs[job_id]["error"] = str(e)

def process_images_with_gemma(image_paths):
    """Process images with Gemma model and return consolidated analysis"""
    if not image_paths:
        return "No images found in the document."
    
    image_analyses = []
    
    for idx, img_path in enumerate(image_paths):
        # Get image metadata
        img_filename = os.path.basename(img_path)
        
        try:
            # Read and encode the image as base64
            with open(img_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Prepare payload with image data for multimodal model
            payload = {
                "model": GEMMA_MODEL_NAME,
                "prompt": "Analyze this scientific figure in detail. Describe what it shows, its significance, and any patterns or trends visible.",
                "images": [image_data],
                "stream": False
            }
            
            # Send request to Gemma
            response = requests.post(GEMMA_SERVER_URL, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "")
                image_analyses.append(f"### Analysis of Figure {idx+1} ({img_filename})\n\n{analysis}\n\n")
            else:
                error_message = f"Failed to analyze image. Status code: {response.status_code}"
                print(f"Error analyzing {img_filename}: {error_message}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    pass
                image_analyses.append(f"### Figure {idx+1} ({img_filename})\n{error_message}\n\n")
        except Exception as e:
            error_message = f"Error processing image: {str(e)}"
            print(f"Exception for {img_filename}: {error_message}")
            image_analyses.append(f"### Figure {idx+1} ({img_filename})\n{error_message}\n\n")
    
    # Combine all analyses into a single document
    combined_analysis = "# Image Analysis Summary\n\n" + "\n".join(image_analyses)
    return combined_analysis

def generate_summary_with_deepseek(text_content, image_analysis):
    """Generate a comprehensive summary using Deepseek model"""
    # Prepare the combined input
    combined_input = f"""
    # Original Document Text
    
    {text_content}
    
    # Image Analysis
    
    {image_analysis}
    """
    
    # Prepare the prompt for Deepseek
    prompt = f"""
    You are an AI research assistant specialized in creating comprehensive summaries of scientific papers.
    You have been provided with:
    1. The extracted text from a research paper
    2. An analysis of the figures/images in the paper

    Make sure the output is in two sections - Explaining content and image in corelation and detailed as well
    Your task is to create a technical yet detailed summary that:
    - Captures the main research question or hypothesis
    - Summarizes the methodology used
    - Highlights key findings and their significance
    - Incorporates relevant information from the figures/images
    - Maintains technical accuracy while being accessible
    - Retain most of the technical terms and explanations in brackets
    
    Here is the combined input:
    
    {combined_input}
    
    Please provide a comprehensive technical summary:
    """
    
    # Call Deepseek for summarization
    payload = {
        "model": DEEPSEEK_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(DEEPSEEK_SERVER_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Failed to generate summary.")
        else:
            return f"Error: Failed to generate summary. Status code: {response.status_code}"
    except Exception as e:
        return f"Error generating summary: {str(e)}"

# Add this to your Flask app
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
        
        # Generate a job ID
        job_id = f"job_{int(time.time())}_{filename}"
        
        # Initialize job status
        processing_jobs[job_id] = {
            "status": STATUS_PENDING,
            "filename": filename,
            "created_at": time.time()
        }
        
        # Start background processing thread
        Thread(target=process_pdf_in_background, args=(filepath, filename, job_id)).start()
        
        # Return immediate response to client
        return jsonify({
            'message': 'File uploaded successfully. Processing started in background.',
            'filename': filename,
            'job_id': job_id,
            'status': STATUS_PENDING
        }), 202  # 202 Accepted indicates processing has started but not completed
    else:
        return jsonify({'error': 'File type not allowed. Please upload a PDF file'}), 400

@app.route('/job/status/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Endpoint to check the status of a processing job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job_info = processing_jobs[job_id].copy()
    
    # Calculate processing time
    if 'completed_at' in job_info:
        job_info['processing_time'] = job_info['completed_at'] - job_info['created_at']
    else:
        job_info['processing_time'] = time.time() - job_info['created_at']
    
    return jsonify(job_info)

@app.route('/job/result/<job_id>', methods=['GET'])
def get_job_result(job_id):
    """Endpoint to get the result of a completed job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job_info = processing_jobs[job_id]
    
    if job_info['status'] != STATUS_COMPLETED:
        return jsonify({
            'error': 'Job not completed yet',
            'status': job_info['status']
        }), 400
    
    # Read the summary file
    try:
        with open(job_info['summary_path'], 'r', encoding='utf-8') as f:
            summary = f.read()
        
        return jsonify({
            'job_id': job_id,
            'status': STATUS_COMPLETED,
            'filename': job_info['filename'],
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': f'Failed to read summary: {str(e)}'}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
