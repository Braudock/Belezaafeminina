import os.path
import pickle
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def autenticar_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials_oauth.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def responder_email(service, message_id_original, destinatario, assunto, corpo):
    original_message = service.users().messages().get(userId='me', id=message_id_original).execute()
    thread_id = original_message['threadId']

    message = MIMEText(corpo)
    message['To'] = destinatario
    message['Subject'] = "Re: " + assunto
    message['In-Reply-To'] = message_id_original
    message['References'] = message_id_original

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    response = service.users().messages().send(
        userId='me',
        body={
            'raw': raw,
            'threadId': thread_id
        }
    ).execute()

    print("✅ E-mail enviado! ID:", response['id'])
    return response

def main():
    creds = autenticar_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Pega o último e-mail recebido
    results = service.users().messages().list(userId='me', maxResults=1, q="from:braudock01@gmail.com").execute()
    messages = results.get('messages', [])

    if not messages:
        print("❌ Nenhum e-mail de Braudock01@gmail.com encontrado.")
        return

    message_id = messages[0]['id']
    message_data = service.users().messages().get(userId='me', id=message_id, format='metadata').execute()

    # Extrai o assunto
    headers = message_data['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem Assunto')

    # Responde com "Bom dia!"
    responder_email(service, message_id, "braudock01@gmail.com", subject, "Bom dia!")

if __name__ == '__main__':
    main()
