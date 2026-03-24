from fastapi import APIRouter
from pydantic import BaseModel
from rag_pipeline.rag.prompt import build_prompt
from rag_pipeline.rag.retrieval import retrieve_context
from rag_pipeline.rag.llm import generate_answer

router = APIRouter()

class Query(BaseModel):
    question: str

@router.post('/chat/query')
def chat_query(question: Query):
    context = retrieve_context(question.question)
    print(context)
    # if not context:
    #     return {"answer": "I don't know"}
        
    prompt = build_prompt(context, question)
    answer = generate_answer(prompt)

    return {"answer": answer}