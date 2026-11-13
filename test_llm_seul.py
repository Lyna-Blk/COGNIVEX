import os
import requests

question = """A completely fictional 15-year-old patient has been taking Mibral (amlodipine, an antihypertensive) long term and asks a pharmacist about Doliprane (paracetamol, an analgesic/antipyretic) for pain.

1. What is the INN of Doliprane?
2. Is there a documented interaction between paracetamol and amlodipine? If so, state its level and cite the source. If you find no interaction, do not claim that this proves there is no risk.
3. What precautions for a 15-year-old are explicitly stated in the official product information for the relevant products? Do not calculate a personalized dose.
4. If Doliprane is unavailable, list products registered in Algeria with the same active ingredient, dosage form, and strength. Do not recommend replacing one product with another.
5. For each answer, give the source title, date, and exact section. If you cannot verify a fact or source, say so clearly.

Do not diagnose or prescribe. This is a fictional documentation exercise, and no source documents are provided."""

key = os.environ.get("GROQ_API_KEY")
if not key:
    raise SystemExit("GROQ_API_KEY absente dans ce terminal.")

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}"},
    json={
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": question}],
    },
    timeout=60,
)

print("Code HTTP :", response.status_code)
response.raise_for_status()

answer = response.json()["choices"][0]["message"]["content"]
print(answer)