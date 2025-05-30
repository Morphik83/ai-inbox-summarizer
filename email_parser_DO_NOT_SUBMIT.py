import os
import imaplib
import email
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime, timedelta
import dateutil.parser

# Load environment variables
load_dotenv()

class EmailParser:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        self.prompt = PromptTemplate(
            input_variables=["emails"],
            template="""Analyze the following emails and provide a concise summary.
            Focus on important information and action items.
            Format the summary in bullet points.
            
            Emails:
            {emails}
            
            Summary:"""
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def connect_to_email(self):
        """Connect to email server and return connection"""
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        mail.select('inbox')
        return mail

    def fetch_recent_emails(self, mail, days=7):
        """Fetch emails from the last X days"""
        date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'SINCE {date}')
        
        emails = []
        for num in messages[0].split():
            _, msg = mail.fetch(num, '(RFC822)')
            email_message = email.message_from_bytes(msg[0][1])
            
            # Extract basic email info
            subject = email_message['subject']
            sender = email_message['from']
            
            # Get email body
            if email_message.is_multipart():
                body = ''
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            emails.append({
                'subject': subject,
                'sender': sender,
                'body': body
            })
        
        return emails

    def generate_summary(self, emails):
        """Generate AI summary of emails"""
        email_text = "\n\n".join([
            f"Subject: {e['subject']}\nFrom: {e['sender']}\n\n{e['body']}"
            for e in emails
        ])
        
        return self.chain.run(emails=email_text)

    def send_summary_email(self, summary):
        """Send the summary email"""
        msg = MIMEText(summary)
        msg['Subject'] = "Daily Email Summary"
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = os.getenv('EMAIL_USER')
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)

    def run(self):
        """Main function to run the email parsing process"""
        try:
            mail = self.connect_to_email()
            emails = self.fetch_recent_emails(mail)
            summary = self.generate_summary(emails)
            self.send_summary_email(summary)
            print("Summary email sent successfully!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            mail.logout()

if __name__ == "__main__":
    parser = EmailParser()
    parser.run()
