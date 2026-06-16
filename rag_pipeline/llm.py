from openai import OpenAI
from config import OPENROUTER_API_KEY
import os

MODEL = "deepseek/deepseek-v4-flash"
REWRITE_MODEL = "meta-llama/llama-3.3-70b-instruct"

SYSTEM_PROMPT = """You are a helpful assistant for COMSATS University Islamabad, Sahiwal Campus.
Your job is to answer student questions accurately using ONLY the exact information provided in the context below.

Strict Rules:
- Don't add any special characters, emojis or formatting in your answer — just plain text.
- Keep answers clear, concise and friendly.
- NEVER make up numbers, fees, percentages or dates — only use exact values from the context.
- Always mention specific amounts, percentages, or dates when available
- Always mention if figures are subject to change
- Do not add any information that is not explicitly in the context
- If a user asks a question unrelated to the university, politely respond: "This chatbot is intended for university-related inquiries only. Please ask a question related to university services, departments, faculty, courses, or student support."

When you don't know something, respond naturally based on what was asked:
for example:
- Unknown person → "I don't have any information about [name]."
- Unknown password/access → "I don't have access to that information."
- Exam schedule/results → "I don't have the current exam schedule. Please check the university portal or contact your department."
- General unknown → "I don't have information about that. You may want to contact the relevant department directly."

Never use the same canned response every time. Adapt your "I don't know" reply to fit what the student actually asked.
Do NOT say "Please contact the Student Support Center" for every unknown — only say it when it genuinely makes sense.
"""


def get_answer(question: str, chunks: list[dict],
               history: list[dict] = None) -> dict:
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

        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
                source = chunk.get("metadata", {}).get("source", "unknown")
                context_parts.append(f"[Source {i} — {source}]\n{chunk['text']}")
        context = "\n\n".join(context_parts)

        history_text = ""
        if history:
                history_text = "\n".join(
                    f"{m['role'].upper()}: {m['content']}"
                    for m in history[-4:]
                )
        user_prompt = f"""Context information:
            {context}

            {"Previous conversation:" + chr(10) + history_text if history_text else ""}

            Student question: {question}

            Instructions:
            - Answer using ONLY the context information provided above
            - If the previous conversation is related to the current question, use it to better understand what the student is asking
            - If the previous conversation is NOT related to the current question, ignore it completely
            - Never mix up topics from previous conversation with the current question
            - If the answer is not in the context, respond naturally based on what was asked
            - Plain text only, no formatting or special characters
            - Be concise and friendly

            Answer:"""

        messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ]

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.2,
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

def rewrite_query(question: str, history: list[dict]) -> str:
    """
    Uses LLM to rewrite follow-up questions into standalone search queries.
    Falls back to original if rewrite fails.
    """
    if not history or not OPENROUTER_API_KEY:
        return question

    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

        last_user = next(
            (m["content"] for m in reversed(history)
             if m["role"] == "user"), ""
        )
        last_assistant = next(
            (m["content"][:150] for m in reversed(history)
             if m["role"] == "assistant"), ""
        )

        rewrite_prompt = (
            f"You are helping rewrite student questions for a university chatbot.\n\n"
            f"Previous question: {last_user}\n"
            f"Previous answer: {last_assistant}\n"
            f"New message: {question}\n\n"
            f"Rules:\n"
            f"1. If the new message clearly references something from the previous "
            f"conversation (uses words like 'it', 'that', 'what about', 'same', "
            f"'those', 'how much') → rewrite as a standalone question using that context.\n"
            f"2. If the new message is a correction → rewrite to reflect what "
            f"the student actually wants.\n"
            f"3. If the new message is a complete independent question → return "
            f"it exactly as written, do not add extra context.\n"
            f"4. IMPORTANT: Do not assume the new question is related to the "
            f"previous one unless the new message explicitly references it.\n"
            f"5. Return ONLY the final question — no prefixes like "
            f"'Search query:' or 'Standalone:' or quotes.\n"
            f"6. Never return 'None', 'null', or empty text.\n\n"
            f"Final question:"
        )

        response = client.chat.completions.create(
            model=REWRITE_MODEL,
            messages=[{"role": "user", "content": rewrite_prompt}],
            max_tokens=64,
            temperature=0.0,
        )

        content = response.choices[0].message.content
        if not content:
            print("[QUERY REWRITE] Empty response — using original")
            return question

        rewritten = content.strip()

        # Strip quotes
        rewritten = rewritten.strip('"').strip("'").strip()

        # Strip common prefixes models add
        prefixes_to_remove = [
            "search query:", "standalone question:", "rewritten:",
            "final question:", "query:", "answer:",
        ]
        rewritten_lower = rewritten.lower()
        for prefix in prefixes_to_remove:
            if rewritten_lower.startswith(prefix):
                rewritten = rewritten[len(prefix):].strip().strip('"').strip("'")
                break

        # Safety fallback
        if (not rewritten or
            rewritten.lower() in ("none", "null", "") or
            len(rewritten) < 4 or
            len(rewritten) > 200):
            print(f"[QUERY REWRITE] Bad response '{rewritten}' — using original")
            return question

        print(f"[QUERY REWRITE] '{question}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        print(f"[QUERY REWRITE ERROR] {e}")
        return question
