# 📚 AutoResearcher – Autonomous Paper & Knowledge Summarization Agent

AutoResearcher is an autonomous research assistant built with AutoGen and OpenAI Function Calling that can search, download, read, and summarize academic papers from arXiv and articles from Wikipedia.

It allows you to ask high-level research questions and receive structured summaries without manually hunting for sources.

## ✨ Features

### 🔍 Intelligent Search

Queries arXiv for academic papers

Queries Wikipedia for related articles

### 🤖 Agent-Driven Orchestration

Powered by AutoGen multi-agent framework

Uses OpenAI function calling for tool execution and decision making

### 📄 Automated Document Handling

Downloads PDFs from arXiv and Wikipedia

Extracts and cleans text

### 🧠 LLM-Based Summarization

Produces concise summaries of papers and articles

Supports long-document chunking

🗂 Source-Aware Output

Each summary includes title, authors, publication date, and URL

## 🚀 Getting Started

1. Clone the repository

```

git clone https://github.com/debin2025/AutoResearcher.git
cd autoresearcher

```

2. Install dependencies

```

pip install -r requirements.txt

```

3. Configure API Key

```

export OPENAI_API_KEY="your_api_key_here"

```

4. Run the Agent

```

python -m src.main

```

## 🧪 Example

```

Find me 5 wiki articles on chinese emperors.

```

Agent execution:

Calls query_arxiv() or query_wikipedia() to retrieve relevant articles

Downloads and parses PDFs

Produces a consolidated summary
