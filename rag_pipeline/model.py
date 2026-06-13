# """
# Shared SentenceTransformer model for RAG modules.
# Loaded once by Python's import cache and reused by searcher/embedder.
# """

# from sentence_transformers import SentenceTransformer

# EMBED_MODEL = "all-MiniLM-L6-v2"

# print("[RAG] Loading SentenceTransformer model...")
# model = SentenceTransformer(EMBED_MODEL)
# print("[RAG] SentenceTransformer model ready.")
