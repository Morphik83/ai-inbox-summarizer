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
            body = ""
            print(f"DEBUG: Summarizing email: {subject}\n{'-'*40}")
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode(errors='ignore')
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')
            emails_formatted.append(f"Subject: {subject}\nBody: {body}")

        combined = "\n\n---\n\n".join(emails_formatted)
        prompt = f"""
You are an expert financial analyst and writer. Read the following email/report and produce a layman-friendly summary with these sections:

---
## 📜 What Happened?
- Briefly explain the main news or ruling.

## 🔮 What’s Next?
- Predict possible next steps or consequences.

## 💰 Money Matters
- Explain financial impacts (refunds, debt, tax plans, etc).

## 📉 Market Reactions
- Note how markets, bonds, and USD reacted.
- FX (DXY,EUR/USD, GBP/USD, USD/CHF, USD/JPY)

## 🧠 Takeaways
- Summarize the key points in a table.

---
Here is the email/report:
{combined}
"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
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