import requests
import json

# Define the endpoint URL
url = "https://trivially-humble-anemone.ngrok-free.app/summarize"

# Long text to test the summarizer
long_text = """
Mercedes-Benz is a globally recognized luxury automobile brand that has set the benchmark for engineering excellence, 
performance, and innovation in the automotive industry. The brand's history dates back over a century, making it one of 
the pioneers in the modern automobile industry. Mercedes-Benz has consistently been at the forefront of technological 
advancements, introducing groundbreaking innovations such as the Anti-lock Braking System (ABS), Electronic Stability 
Program (ESP), and cutting-edge autonomous driving technologies.

The company’s flagship models, such as the S-Class, G-Class, and AMG performance lineup, have redefined the standards of 
luxury, safety, and high performance. Additionally, the Mercedes-AMG Petronas Formula One Team has dominated motorsports 
for years, securing multiple championship titles with legendary drivers.

As the automotive industry transitions towards sustainable mobility, Mercedes-Benz has launched its EQ lineup of 
electric vehicles, including the EQS and EQB, which showcase advanced battery technology and a commitment to carbon-neutral 
manufacturing by 2039.

Today, Mercedes-Benz continues to lead the industry by integrating artificial intelligence, smart driving assistance 
systems, and fully electric powertrains, maintaining its legacy as a premier automobile manufacturer.
"""

# Prepare the request payload
payload = json.dumps({"text": long_text})
headers = {"Content-Type": "application/json"}

# Send POST request with streaming enabled
with requests.post(url, data=payload, headers=headers, stream=True) as response:
    for chunk in response.iter_content(chunk_size=1024):  # Stream the response in chunks
        if chunk:
            print(chunk.decode(), end='', flush=True)  # Print streamed response in real-time