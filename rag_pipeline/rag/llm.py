import google.generativeai as genai

genai.configure(api_key='AIzaSyA6A-kUIXSXygzrJ5d7y6g0hWKGoSSaBts')

model = genai.GenerativeModel('gemini-2.5-flash')

def generate_answer(prompt: str) -> str:
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0}
        )

        if hasattr(response, "text") and response.text:
            return response.text

        return "I don't know"

    except Exception as e:
        print("Gemini error:", e)
        return "I don't know"