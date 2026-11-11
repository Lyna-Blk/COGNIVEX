import os
import requests

cle = os.environ["GROQ_API_KEY"]

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {cle}"},
    json={
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "user", "content": "Réponds juste : OK"}
        ],
    },
    timeout=60,
)

print(r.status_code)
print(r.json()["choices"][0]["message"]["content"])