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
- Streamlit
- LangChain
- ChromaDB
- Ollama
- Tesseract OCR

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/AdeshSrivastava-06/Omni-recall-GD.git
cd Omni-recall-GD
```

## 2. Create a Virtual Environment (Recommended)

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Install Ollama

Download and install Ollama from:

https://ollama.com/download

After installation, pull the required model:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

> Make sure the Ollama server is running before starting the application.

## 5. Install Tesseract OCR

Download and install Tesseract OCR.

During installation, ensure it is added to your system PATH.

---

# Running the Project

## Step 1: Start the Screenshot Capture Backend

```bash
python capture_deamon.py
```

This continuously captures screenshots, performs OCR, and stores searchable embeddings locally.

---

## Step 2: Start the Streamlit Application

Open a new terminal and run:

```bash
streamlit run App.py
```

This launches the user interface where you can search your screen history using natural language.


