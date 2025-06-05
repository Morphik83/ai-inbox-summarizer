import os
import imaplib
from datetime import datetime, timedelta
from openai import OpenAI
import email
import time

from dotenv import load_dotenv
load_dotenv()


class EmailParserConnect:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
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

    def summarize_emails(self, mail, email_ids):
        emails_formatted = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg['subject'] or '(No Subject)'
            date_header = msg['date']
            # Try to parse the date header
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_header) if date_header else datetime.now()
            except Exception:
                dt = datetime.now()
            weekday = dt.strftime('%a')
            time_str = dt.strftime('%H:%M')
            html_body = ""
            # Add visual separation and header
            print("\n\n\n" + f"[{weekday}][{time_str}][{subject}]\n" + "-"*40)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html_body += part.get_payload(decode=True).decode(errors='ignore')
            else:
                if msg.get_content_type() == "text/html":
                    html_body = msg.get_payload(decode=True).decode(errors='ignore')
            # Extract and clean HTML (only after collecting all parts)
            if html_body:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_body, 'html.parser')
                for tag in soup(["script", "style"]):
                    tag.decompose()
                body = soup.get_text(separator="\n")
                body = '\n'.join([line.strip() for line in body.splitlines() if line.strip()])
            else:
                body = "[No HTML body found]"
            emails_formatted.append(f"[{weekday}][{time_str}][{subject}]\n\nSubject: {subject}\nBody: {body}")

        combined = "\n\n---\n\n".join(emails_formatted)
        prompt = f"""
You are an expert financial analyst and macroeconomist. Your job is to read the following email/report and produce a deep-dive, layman-friendly summary with actionable insights. 

**Instructions:**
- Do NOT just repeat headlines or bullet points.
- Analyze the underlying causes, market context, and potential consequences.
- Compare to recent trends or similar events if relevant.
- Highlight what is surprising, counterintuitive, or most important for investors.
- Use markdown, tables, and emojis for clarity.
- Each section should contain original analysis, not repetition.
- Always try to explain in a layman-friendly economic concepts that are mentioned in the email.

---
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
Give a bottom-line, plain-English explanation of the economy-concepts that are mentioned in the email.

---
Here is the email/report:
{combined}
"""
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst and writer. Respond in clear, structured, layman-friendly language, using markdown and emojis for clarity."},
                {"role": "user", "content": prompt}
            ]
        )
        print(response.choices[0].message.content)

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

if __name__ == "__main__":
    parser_connect = EmailParserConnect()
    parser_connect.poll_for_new_emails(poll_interval=120)