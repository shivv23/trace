# Trace Documentation

## Getting Started

Welcome to Trace! This guide will help you set up and use the platform effectively.

### Installation

To install Trace, follow these steps:

1. Clone the repository from GitHub
2. Install Python dependencies using pip install -r requirements.txt
3. Copy .env.example to .env and add your API keys
4. Run the backend with uvicorn app.main:app --reload
5. In a separate terminal, install frontend dependencies with npm install
6. Start the frontend with npm run dev

### System Requirements

- Python 3.11 or higher
- Node.js 18 or higher
- At least 4 GB of RAM recommended
- Operating System: Windows, macOS, or Linux

## Features

### Multi-Format Document Ingestion

Trace supports uploading documents in multiple formats:
- PDF files for product documentation and manuals
- DOCX files for Word documents and reports
- TXT files for plain text content
- Markdown files for documentation
- JSON files for structured data
- CSV files for tabular data
- HTML files for web content

Each uploaded document is automatically parsed, chunked into segments, and indexed for search.

### Transparent AI Responses

Unlike traditional chatbots that return black-box answers, Trace shows its work. Every response includes:

- Cited sources with document names
- Relevance scores for each source
- A confidence gauge showing overall answer reliability
- Expandable source content for verification

### Confidence Scoring

Trace uses a multi-factor confidence scoring system:

- Relevance Score (35%): How relevant the retrieved chunks are to the query
- Semantic Similarity (25%): How well the answer aligns with the query meaning
- Source Quality (20%): Diversity and consistency of supporting sources
- Support Ratio (20%): How many chunks support the answer

Confidence levels:
- High (75%+): Answer is reliable and well-supported
- Medium (45-74%): Answer may need verification
- Low (below 45%): Better to consult a human agent

### Feedback System

Users can rate responses with thumbs up or thumbs down. This feedback is logged and can be used to improve response quality over time. Support teams can review low-rated responses to identify knowledge gaps.

### Content Safety

Trace includes built-in safety features:
- PII redaction removes sensitive information from responses
- Content moderation filters toxic or abusive input
- Rate limiting prevents abuse

## API Integration

### Chat Endpoint

Send messages to the chat endpoint to get AI-powered responses:

POST /api/chat

The request requires a message field with your question. You can optionally provide a conversation_id to continue an existing conversation.

### Document Management

Upload documents through the API or the web interface:

POST /api/documents/upload

Supported file types include PDF, DOCX, TXT, MD, JSON, CSV, and HTML. Maximum file size is 20 MB.

## Troubleshooting

### Common Issues

**Issue: No documents are being indexed**
Solution: Make sure your file is under 20 MB and in a supported format. Check that the uploads directory exists.

**Issue: API is returning 503 errors**
Solution: The chat engine requires at least one document to be uploaded first. Upload a document and try again.

**Issue: LLM responses are empty**
Solution: Check that your API keys are correctly configured in the .env file. If both Gemini and Groq keys are missing, the system will run in offline mode with extractive responses.

**Issue: Slow response times**
Solution: Response time depends on the number of indexed documents. For best performance, keep your knowledge base focused and well-organized.
