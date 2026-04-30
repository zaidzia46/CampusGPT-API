from openai import OpenAI
from config import OPENROUTER_API_KEY

MODEL = "deepseek/deepseek-v4-flash"

SYSTEM_PROMPT = """You are a helpful assistant for COMSATS University Islamabad, Sahiwal Campus.
Your job is to answer student questions accurately using ONLY the exact information provided in the context below.

Strict Rules:
- Don't add any special characters, emojis or formatting in your answer — just plain text.
- NEVER make up numbers, fees, percentages or dates — only use exact values from the context
- If the exact answer is not clearly stated in the context, say: "I don't have that information. Please contact the Student Support Center at COMSATS Sahiwal Campus."
- Copy fee amounts and percentages exactly as they appear in the context — do not calculate or estimate
- Keep answers clear, concise and friendly
- Always mention if figures are subject to change
- Do not add any information that is not explicitly in the context
"""


def build_prompt(question: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("metadata", {}).get("source", "unknown")
        context_parts.append(f"[Source {i} — {source}]\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    return f"""Use the following information to answer the student's question.

Context:
{context}

Student Question: {question}

Answer:"""


def get_answer(question: str, chunks: list[dict]) -> dict:
    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "answer":  "LLM API key not configured.",
            "model":   MODEL,
        }

    if not chunks:
        return {
            "success": True,
            "answer":  "I don't have that information. Please contact the Student Support Center.",
            "model":   MODEL,
        }

    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

        prompt = build_prompt(question, chunks)

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=512,
            temperature=0.2,   # low = more factual, less creative
        )

        answer = response.choices[0].message.content.strip()

        return {
            "success": True,
            "answer":  answer,
            "model":   MODEL,
        }

    except Exception as e:
        print(f"[LLM ERROR] {type(e).__name__}: {e}")
        return {
            "success": False,
            "answer":  "Sorry, I couldn't process your question right now. Please try again.",
            "model":   MODEL,
            "error":   str(e),
        }