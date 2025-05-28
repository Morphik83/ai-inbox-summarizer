import os
import imaplib
import email
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from langchain.llms import OpenAI
from datetime import datetime, timedelta
import dateutil.parser

# Load environment variables
load_dotenv()

class EmailSummarizer:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        self.email_summary = ""

    def connect_to_email(self):
        """Connect to the email server"""
        try:
            mail = imaplib.IMAP4_SSL(os.getenv('IMAP_SERVER'))
            mail.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            mail.select('inbox')
            return mail
        except Exception as e:
            print(f"Error connecting to email: {e}")
            raise

    def fetch_recent_emails(self, mail, days=7):
        """Fetch emails from the last X days"""
        try:
            # Search for emails from the last X days
            since_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
            _, messages = mail.search(None, f'SINCE "{since_date}"')
            return messages[0].split()
        except Exception as e:
            print(f"Error fetching emails: {e}")
            raise

    def parse_email(self, mail, email_id):
        """Parse a single email"""
        try:
            _, msg = mail.fetch(email_id, '(RFC822)')
            email_body = msg[0][1]
            mail = email.message_from_bytes(email_body)
            
            subject = mail['subject']
            sender = mail['from']
            date = mail['date']
            
            # Get the email body
            body = ""
            if mail.is_multipart():
                for part in mail.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = mail.get_payload(decode=True).decode()
            
            return {
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body
            }
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None

    def generate_summary(self, emails):
        """Generate a summary using AI"""
        if not emails:
            return "No new emails found."
            
        email_texts = []
        for email in emails:
            email_texts.append(f"Subject: {email['subject']}\nFrom: {email['sender']}\nDate: {email['date']}\n\n{email['body'][:1000]}...")
            
        summary_prompt = f"""Please analyze these emails and provide a concise summary of their main points and any important actions needed. Focus on the most relevant information.

Emails:
{'\n\n---\n\n'.join(email_texts)}

Summary:"""
        
        self.email_summary = self.llm(summary_prompt)
        return self.email_summary

    def send_summary_email(self):
        """Send the summary email"""
        try:
            msg = MIMEText(self.email_summary)
            msg['Subject'] = 'Your Daily Email Summary'
            msg['From'] = os.getenv('EMAIL_USER')
            msg['To'] = os.getenv('EMAIL_USER')
            
            with smtplib.SMTP_SSL(os.getenv('SMTP_SERVER'), 465) as server:
                server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
                server.send_message(msg)
            
            print("Summary email sent successfully!")
        except Exception as e:
            print(f"Error sending summary email: {e}")
            raise

    def run(self):
        """Main execution method"""
        try:
            mail = self.connect_to_email()
            email_ids = self.fetch_recent_emails(mail)
            
            if not email_ids:
                print("No new emails found.")
                return
                
            emails = []
            for email_id in email_ids:
                email_data = self.parse_email(mail, email_id)
                if email_data:
                    emails.append(email_data)
            
            summary = self.generate_summary(emails)
            self.send_summary_email()
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if 'mail' in locals():
                mail.logout()

if __name__ == "__main__":
    summarizer = EmailSummarizer()
    summarizer.run()
