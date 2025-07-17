import os
import imaplib
from datetime import datetime, timedelta, time as dtime
from openai import OpenAI
import email
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()


class EmailParserConnect:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.summary_recipient = os.getenv('SUMMARY_RECIPIENT', self.email_user)
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )


    def connect_to_email(self):
        """Connect to email server and return connection"""
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(self.email_user, self.email_password)
        mail.select('inbox')
        return mail

    def fetch_today_emails(self, mail):
        """Fetch emails from today only"""
        today = datetime.now().strftime("%d-%b-%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'SINCE "{today}" BEFORE "{tomorrow}"')
        return messages[0].split()

    def fetch_last_24h_emails(self, mail):
        """Fetch emails from the last 24 hours"""
        since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'SINCE "{since}"')
        return messages[0].split()


    def summarize_emails(self, mail, email_ids, return_summary=False):
        from email.header import decode_header
        from email.utils import parsedate_to_datetime
        from bs4 import BeautifulSoup
        def decode_mime_words(s):
            if not s:
                return '(No Subject)'
            decoded_parts = decode_header(s)
            return ''.join([
                part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
                for part, enc in decoded_parts
            ])
        emails_formatted = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_mime_words(msg['subject'])
            date_header = msg['date']
            try:
                dt = parsedate_to_datetime(date_header) if date_header else None
            except Exception:
                dt = None
            dt_str = dt.strftime('%m-%d %H:%M') if dt else '[No Date]'
            html_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html_body += part.get_payload(decode=True).decode(errors='ignore')
            else:
                if msg.get_content_type() == "text/html":
                    html_body = msg.get_payload(decode=True).decode(errors='ignore')
            if html_body:
                soup = BeautifulSoup(html_body, 'html.parser')
                for tag in soup(["script", "style"]):
                    tag.decompose()
                body = soup.get_text(separator="\n")
                body = '\n'.join([line.strip() for line in body.splitlines() if line.strip()])
            else:
                body = "[No HTML body found]"
            emails_formatted.append(f"[{dt_str}] {subject}\n{body}")
        combined = '\n\n---\n\n'.join(emails_formatted)
        prompt = f"""
You are an expert financial analyst and macroeconomist. Your job is to read the following set of emails/reports (from the last 24h) and produce a SINGLE, concise, deep-dive, layman-friendly one-pager summary with actionable insights. 

**Instructions:**
- Synthesize and compare across all emails. Do NOT just summarize each one separately.
- Focus on what is most important, surprising, or actionable for investors.
- Analyze the underlying causes, market context, and potential consequences.
- Compare to recent trends or similar events if relevant.
- Use markdown, tables, and emojis for clarity.
- Each section should contain original analysis, not repetition.
- Always try to explain in a layman-friendly economic concepts that are mentioned in the emails.
- The result should be a single one-pager, not a list of per-email summaries.

----
### 🧾 Main Takeaways
Summarize the key points, but add your own expert interpretation and context.

### 💰 Market Implications
Explain how this news might affect markets (FX, bonds, stocks, etc.), with reasoning and comparisons to similar past events.

### 🔍 Key Economic Context
Describe the broader economic background, trends, and drivers. What is different or notable here?

### ⚠️ Risks & Uncertainties
List major risks, uncertainties, or things to watch for, explaining why they matter.

### 📝 Final Thoughts (Simple Terms)
Give a bottom-line, plain-English summary for a non-expert, focusing on what to watch next and why.

### 📝 Economy-concepts explanation
Give a bottom-line, plain-English explanation of the economy-concepts that are mentioned in the emails.

----
Here are the emails/reports:
{combined}
"""
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst and writer. Respond in clear, structured, layman-friendly language, using markdown and emojis for clarity."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content
        if return_summary:
            return summary
        print(summary)


    def poll_for_new_emails(self, poll_interval=120):
        print("Starting email polling...")
        last_seen = set()
        while True:
            mail = self.connect_to_email()
            email_ids = self.fetch_today_emails(mail)
            new_emails = [eid for eid in email_ids if eid not in last_seen]
            if new_emails:
                print(f"Detected {len(new_emails)} new email(s)!")
                self.summarize_emails(mail, new_emails)
            last_seen = set(email_ids)
            mail.logout()
            time.sleep(poll_interval)

    def send_email(self, subject, body, recipient=None):
        recipients = recipient or self.summary_recipient
        # Support comma-separated emails in env
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(',') if r.strip()]
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, recipients, msg.as_string())
            print(f"Summary email sent to {recipients}!")
        except Exception as e:
            print(f"Failed to send summary email: {e}")

    def run_daily_summary_scheduler(self):
        print("Daily summary scheduler started. Will send at 21:00 each day.")
        while True:
            now = datetime.now()
            target = now.replace(hour=21, minute=0, second=0, microsecond=0)
            if now > target:
                target += timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            print(f"Waiting {int(wait_seconds)} seconds until next summary at 21:00...")
            time.sleep(wait_seconds)
            try:
                self.send_daily_summary_now()
            except Exception as e:
                print(f"Error in daily summary scheduler: {e}")

    def send_daily_summary_now(self):
        print("Sending daily summary now (testing mode)...")
        mail = self.connect_to_email()
        email_ids = self.fetch_last_24h_emails(mail)
        if not email_ids:
            print("No emails found in the last 24 hours for summary.")
            return
        summary = self.summarize_emails(mail, email_ids, return_summary=True)
        # Build the analyzed emails list
        from email.header import decode_header
        from email.utils import parsedate_to_datetime
        def decode_mime_words(s):
            if not s:
                return '(No Subject)'
            decoded_parts = decode_header(s)
            return ''.join([
                part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
                for part, enc in decoded_parts
            ])
        analyzed_list = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_mime_words(msg['subject'])
            date_header = msg['date']
            try:
                dt = parsedate_to_datetime(date_header) if date_header else None
            except Exception:
                dt = None
            dt_str = dt.strftime('%m-%d %H:%M') if dt else '[No Date]'
            analyzed_list.append(f"- {dt_str} | {subject}")
        analyzed_section = "\n\n---\n\n**Analyzed Emails (last 24h):**\n" + '\n'.join(analyzed_list)
        summary_with_list = summary + analyzed_section
        self.send_email(
            subject=f"Daily Email Summary ({datetime.now().strftime('%Y-%m-%d')})",
            body=summary_with_list,
            recipient=self.summary_recipient
        )
        mail.logout()

    def list_daily_summary_email_titles(self):
        print("Listing email subjects and timestamps for the daily summary (last 24h):")
        mail = self.connect_to_email()
        email_ids = self.fetch_last_24h_emails(mail)
        if not email_ids:
            print("No emails found in the last 24 hours.")
            mail.logout()
            return
        from email.utils import parsedate_to_datetime
        from email.header import decode_header
        def decode_mime_words(s):
            if not s:
                return '(No Subject)'
            decoded_parts = decode_header(s)
            return ''.join([
                part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
                for part, enc in decoded_parts
            ])
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_mime_words(msg['subject'])
            date_header = msg['date']
            try:
                dt = parsedate_to_datetime(date_header) if date_header else None
            except Exception:
                dt = None
            dt_str = dt.strftime('%m-%d %H:%M') if dt else '[No Date]'
            print(f"- {dt_str} | {subject}")
        mail.logout()


if __name__ == "__main__":
    parser_connect = EmailParserConnect()
    # Uncomment the next line to run the polling loop as before
    # parser_connect.poll_for_new_emails(poll_interval=120)
    # Run the daily summary scheduler for 21:00
    # parser_connect.run_daily_summary_scheduler()
    # For testing: list emails included in the daily summary
    # parser_connect.list_daily_summary_email_titles()
    # For testing: send the daily summary immediately
    parser_connect.send_daily_summary_now()