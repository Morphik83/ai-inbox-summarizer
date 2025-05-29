# Email Parser & AI Summarizer

This project connects to your email inbox, fetches emails (e.g., from today), and summarizes them using OpenAI's GPT models. It is implemented in `email_parser.py`.

## Features
- Connects to Gmail (or any IMAP) inbox
- Fetches emails from a configurable time window (e.g., today)
- Uses OpenAI API for high-quality, structured summaries
- Markdown-formatted, layman-friendly output
- Environment-based configuration for security

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy `.env_template` to `.env` and fill in your credentials:
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

## Customization
- Adjust the time window or mailbox in `email_parser.py` as needed.
- Edit the prompt in the summarization method for different summary styles.

## Security
- **Never commit your `.env` file** with real credentials. Use `.env_template` for sharing setup instructions.

## License
MIT

