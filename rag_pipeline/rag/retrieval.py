import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rag_pipeline.rag.embeddings import embed

THRESHOLD = 0.3

documents = [
    "The admission fee for BS Computer Science is 50,000 PKR.",
    "The admission fee for BS Mechanical Engineering is 50,000 PKR.",
    "The semester fee must be paid before classes start.",
    "The semster fee can be payed in 2 installments.",
    "The COMSATS Sahiwal campus has a central library.",
    "The library opens from 8 AM to 8 PM."
]

embed_docs = embed(documents)
context = []

def retrieve_context(question, topk=2):
    embed_query = embed([question])
    scores = cosine_similarity(embed_query, embed_docs)[0]
    context = []
    for i in np.argsort(scores)[-topk:][::-1]:
        if scores[i] >= THRESHOLD:
            context.append(documents[i])

    return context