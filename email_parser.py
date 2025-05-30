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
You are a senior financial analyst. 
You will be given a set of emails containing financial news and market analysis for today.

**Your task:**
- Combine all the information into a single, well-structured summary.
- Eliminate duplicate or redundant points.
- Give special attention to the impact on FX (foreign exchange) markets.
- Pay attention to the impact on the USD.
- Present the summary in clear, concise, layman-friendly language.
- Use markdown formatting with sections for: Main Events, FX Market Impact, and Key Takeaways.

Here are today's emails:
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

    def poll_for_new_emails(self, poll_interval=60):
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