
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import configparser
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

app = FastAPI()

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read("config.ini")

try:
    settings = config['SETTINGS']
except KeyError:
    settings = {}

# Load settings from config
API = settings.get("APIKEY", None)
from_email = settings.get("FROM", None)

class EmailRequest(BaseModel):
    to_emails: list[EmailStr]
    subject: str
    html_content: str

def sendMail(API, from_email, to_emails, subject, html_content):
    if API and from_email and to_emails:
        message = Mail(from_email, to_emails, subject, html_content)
        try:
            sg = SendGridAPIClient(API)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
            return response.status_code
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email/")
async def send_email(request: EmailRequest):
    if not API or not from_email:
        raise HTTPException(status_code=500, detail="API key or from_email not configured")

    status_code = sendMail(API, from_email, request.to_emails, request.subject, request.html_content)
    if status_code == 202:
        return {"status": "success", "message": "Email sent successfully!"}
    else:
        raise HTTPException(status_code=status_code, detail="Failed to send email")

# Example: Run with uvicorn main:app --reload
