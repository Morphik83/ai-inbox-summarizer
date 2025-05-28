# Email Summarizer

This program automatically parses your inbox and generates a summary of your emails using AI. It then sends you a concise summary via email.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following variables:
```
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-email-password
IMAP_SERVER=imap.your-email-provider.com
SMTP_SERVER=smtp.your-email-provider.com
OPENAI_API_KEY=your-openai-api-key
```

## Usage

Run the program:
```bash
python email_summarizer.py
```

The program will:
1. Connect to your email inbox
2. Fetch recent emails (last 7 days by default)
3. Use AI to generate a summary of your emails
4. Send you the summary via email

## Features

- Secure email access using IMAP
- AI-powered email summarization using OpenAI
- Automatic email sending via SMTP
- Handles both plain text and HTML emails
- Configurable via environment variables
