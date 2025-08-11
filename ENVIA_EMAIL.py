import os
import base64
import pickle
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def autenticar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials_oauth.json', SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def enviar_email(service, destinatario, assunto, corpo):
    message = MIMEText(corpo)
    message['to'] = destinatario
    message['subject'] = assunto
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()

# Execução
if __name__ == '__main__':
    service = autenticar()
    enviar_email(service, 'braudockario@gmail.com', 'Assunto de teste', 'Conteúdo enviado via OAuth')
