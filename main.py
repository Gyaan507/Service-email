from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import configparser
import base64

app = FastAPI()


config = configparser.ConfigParser()
config.read("config.ini")

try:
    settings = config['SETTINGS']
except KeyError:
    settings = {}



API = settings.get("APIKEY", None)
from_email = settings.get("FROM", None)

class EmailRequest(BaseModel):
    to_emails: list[EmailStr]
    subject: str
    html_content: str

def sendMail(API, from_email, to_emails, subject, html_content, attachments=None):
    if API and from_email and to_emails:
        message = Mail(from_email, to_emails, subject, html_content)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                encoded_file = base64.b64encode(attachment['content']).decode()
                attached_file = Attachment(
                    FileContent(encoded_file),
                    FileName(attachment['filename']),
                    FileType(attachment['content_type']),
                    Disposition('attachment')
                )
                message.add_attachment(attached_file)

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
async def send_email(
    to_emails: list[EmailStr],
    subject: str,
    html_content: str,
    files: list[UploadFile] = File(None)
):
    if not API or not from_email:
        raise HTTPException(status_code=500, detail="API key or from_email not configured")
    

    # Process attachments
    attachments = []
    if files:
        for file in files:
            file_content = await file.read()
            attachments.append({
                'filename': file.filename,
                'content': file_content,
                'content_type': file.content_type
            })

    status_code = sendMail(API, from_email, to_emails, subject, html_content, attachments)
    if status_code == 202:
        return {"status": "success", "message": "Email sent successfully!"}
    else:
        raise HTTPException(status_code=status_code, detail="Failed to send email")


