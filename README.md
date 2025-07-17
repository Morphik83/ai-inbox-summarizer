# Email Parser & AI Summarizer

This project connects to your email inbox, fetches emails (e.g., from today), and summarizes them using OpenAI's GPT-4.1 model. All summaries are generated from the full HTML content of emails, ensuring rich and accurate analysis.

## Features
- Connects to Gmail (or any IMAP) inbox
- Fetches emails from a configurable time window (e.g., today or last 24 hours)
- Extracts and cleans the HTML part of each email (ignores plain text)
- Uses BeautifulSoup to remove scripts/styles and extract readable content
- Generates structured, markdown-formatted, layman-friendly financial summaries using OpenAI GPT-4.1
- **Sends a single, holistic daily summary email at 21:00 (9PM) automatically, synthesizing all emails from the last 24 hours into a concise, actionable one-pager**
- Uses GPT-4.1 to generate a layman-friendly, fundamentals-focused, and actionable digest (not per-email summaries)
- Supports manual/test summary sending on demand
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
     SUMMARY_RECIPIENT=recipient@email.com,another@email.com  # Optional, comma-separated for multiple recipients; defaults to EMAIL_USER
     ```
   - For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) if 2FA is enabled.

## Usage

### Daily Automated Summary (Recommended)
By default, the script will send a daily summary email at 21:00 (9PM) every day, containing a **single, synthesized one-pager summary** of all emails received in the last 24 hours:
```bash
python email_parser.py
```
- Leave the script running; it will wait and send the summary at the scheduled time each day.
- The summary is not a list of per-email summaries, but a holistic, high-level digest of all key information and context.

### Manual/Test Run
To send the summary immediately (for testing), temporarily edit the `__main__` section in `email_parser.py`:
```python
# parser_connect.run_daily_summary_scheduler()
parser_connect.send_daily_summary_now()
```
Then run:
```bash
python email_parser.py
```
This will send a summary right away using the last 24 hours of emails.

- The script always uses the HTML part of emails for summarization, ensuring the richest possible content.
- Summaries are sent to the configured recipient via email.

## Customization
- Adjust the time window or mailbox in `email_parser.py` as needed.
- Edit the summarization prompt in the code for different summary styles or analysis depth.

## Security
- **Never commit your `.env` file** with real credentials. Use `.env_template` for sharing setup instructions.
- Rotate your API keys if they are ever exposed.

## License
MIT
