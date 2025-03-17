import requests
import base64

# Path to your image
image_path = "/workspaces/ollama_dsr1_seervice/page_11-image_1.png"

# Read and encode the image
with open(image_path, "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

# Create the API request
url = "http://localhost:11434/api/generate"
payload = {
    "model": "gemma3:4b",
    "prompt": "Describe this image in detail",
    "images": [image_data]
}

# Send the request
response = requests.post(url, json=payload)

# Print the response
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))