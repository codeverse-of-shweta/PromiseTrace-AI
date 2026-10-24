import os
import requests

with requests.post(
    'https://agent.tinyfish.ai/v1/automation/run-sse',
    headers={
        'X-API-Key': os.environ['TINYFISH_API_KEY'],
        'Content-Type': 'application/json',
    },
    json={'url': "https://www.iisc.ac.in/", 'goal': "Visit the official Indian Institute of Science website. Find publicly stated placement statistics, industry partnerships, and internship-related claims. Extract the exact claim text, the page URL, and the year mentioned. Return the results in structured JSON. Do not invent missing information. Do not judge whether claims are true or false."},
    stream=True,
) as response:
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))