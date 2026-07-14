import numpy as np
import ollama
from datetime import datetime, timedelta

from db import get_all_captures, get_captures_in_range

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2:3b"


def get_embedding(text: str):
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return np.array(response["embedding"])


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def detect_time_range(query: str):
    query_lower = query.lower()
    now = datetime.now()

    if "today" in query_lower:
        start = now.replace(hour=0, minute=0, second=0)
        return start.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")

    if "yesterday" in query_lower:
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0)
        end = yesterday.replace(hour=23, minute=59, second=59)
        return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")

    if "this morning" in query_lower:
        start = now.replace(hour=0, minute=0, second=0)
        end = now.replace(hour=12, minute=0, second=0)
        return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")

    if "last hour" in query_lower:
        start = now - timedelta(hours=1)
        return start.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")

    return None


def search_captures(query: str, top_k: int = 3):
    query_embedding = get_embedding(query)

    time_range = detect_time_range(query)
    if time_range:
        start, end = time_range
        candidates = get_captures_in_range(start, end)
    else:
        candidates = get_all_captures()

    if not candidates:
        return []

    scored = []
    for cap in candidates:
        score = cosine_similarity(query_embedding, cap["embedding"])
        scored.append((score, cap))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def answer_question(query: str):
    top_matches = search_captures(query, top_k=3)

    if not top_matches:
        return "No captured data found for that question or time range.", []

    context_blocks = [f"[{cap['timestamp']}] ({cap['app_name']}): {cap['text']}" for _, cap in top_matches]
    context_text = "\n\n".join(context_blocks)

    prompt = f"""You are helping someone recall something from their screen history.
Answer using ONLY the information below.

Respond in this exact format:
SUMMARY: (one clear sentence answering the question directly)
DETAILS: (2-3 bullet points with the specific relevant information)
SOURCE: (which timestamp and app this came from)

If the answer isn't clearly in the information, say so in SUMMARY and leave DETAILS empty.

Captured history:
{context_text}

Question: {query}
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": 300}
    )

    return response["message"]["content"], top_matches


def generate_daily_summary():
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
    end_of_day = now.strftime("%Y-%m-%d %H:%M:%S")

    captures = get_captures_in_range(start_of_day, end_of_day)

    if not captures:
        return "No captures recorded yet today."

    # Cap total text sent to the model so it stays fast
    combined_text = "\n\n".join([f"[{c['timestamp']}] ({c['app_name']}): {c['text'][:300]}" for c in captures])
    combined_text = combined_text[:6000]

    prompt = f"""Based on the captured screen activity below, write a short, friendly summary
of what this person did today. Group similar activities together. Keep it to 4-6 bullet points.

Captured activity:
{combined_text}
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": 300}
    )

    return response["message"]["content"]
