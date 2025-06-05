# Email Parser & AI Summarizer

This project connects to your email inbox, fetches emails (e.g., from today), and summarizes them using OpenAI's GPT-4.1 model. All summaries are generated from the full HTML content of emails, ensuring rich and accurate analysis.

## Features
- Connects to Gmail (or any IMAP) inbox
- Fetches emails from a configurable time window (e.g., today)
- Extracts and cleans the HTML part of each email (ignores plain text)
- Uses BeautifulSoup to remove scripts/styles and extract readable content
- Generates structured, markdown-formatted, layman-friendly financial summaries using OpenAI GPT-4.1
- Environment-based configuration for security

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - Ensure `beautifulsoup4` is included in `requirements.txt`

2. **Configure environment variables:**
   - Create a `.env` file in the project directory with:
     ```
     EMAIL_USER=your-email@gmail.com
     EMAIL_PASSWORD=your-app-password
     OPENAI_API_KEY=your-openai-api-key
     ```
   - For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) if 2FA is enabled.

## Usage

Run the script to fetch and summarize today's emails:
```bash
python email_parser.py
```
- The script will always use the HTML part of emails for summarization, ensuring the richest possible content.
- No debug output is printed; only the final summary appears in the console.

## Customization
- Adjust the time window or mailbox in `email_parser.py` as needed.
- Edit the summarization prompt in the code for different summary styles or analysis depth.

## Security
- **Never commit your `.env` file** with real credentials. Use `.env_template` for sharing setup instructions.
- Rotate your API keys if they are ever exposed.

## License
MIT
