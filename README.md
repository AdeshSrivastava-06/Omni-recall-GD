# OmniRecall

OmniRecall is an open-source, privacy-first desktop application that creates a searchable memory of your screen activity using completely offline AI. It periodically captures screenshots, extracts text using OCR, stores embeddings locally, and allows users to search past screen content using natural language.

## Problem

Important information often disappears from our screens before we have a chance to save it, such as chat messages, browser tabs, meeting notes, or terminal outputs. Finding this information later is difficult.

## Solution

OmniRecall continuously captures screenshots, performs local OCR, indexes the extracted text, and uses Retrieval-Augmented Generation (RAG) to answer user queries. All processing happens on the user's device without sending any data to the cloud.

## Features

- Automatic screen capture
- Local OCR using Tesseract
- Semantic search over screen history
- Local vector database using ChromaDB
- Natural language question answering
- Fully offline and privacy-focused

## Tech Stack

- Python
- FastAPI
- React
- Tauri
- LangChain
- ChromaDB
- Ollama
- Tesseract OCR
