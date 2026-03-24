def build_prompt(context, question):
    context_text = "\n".join(context)
    return f"""
    Answer the question using ONLY the context below.
    - If you feel that question is not about university, you can reply
    that the chatbot is specifically designed for University related queries in a friendly way.
    - If you feel that the context is not related to question, then friendly reply with that i dont know about it.

    Context:
    {context_text}

    Question:
    {question}
    """