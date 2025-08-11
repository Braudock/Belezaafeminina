import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
import tkinter as tk
from tkinter import filedialog

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Escopo da API do Gmail: permissão para enviar e-mails.
# Se alterar os escopos, apague o arquivo token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def autenticar_gmail():
    """
    Realiza a autenticação com a API do Gmail, cuidando do fluxo de OAuth 2.0.
    Cria ou atualiza o arquivo token.pickle com as credenciais do usuário.
    Retorna um objeto 'service' para interagir com a API.
    """
    creds = None
    # O arquivo token.pickle armazena os tokens de acesso e atualização do usuário.
    # Ele é criado automaticamente na primeira vez que o fluxo de autorização é concluído.
    if os.path.exists('token.pickle'):
        creds = Credentials.from_authorized_user_file('token.pickle', SCOPES)
    
    # Se não houver credenciais (válidas), permite que o usuário faça login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Usa o arquivo credentials_oauth.json que você já possui.
            if not os.path.exists('credentials_oauth.json'):
                print("Erro: Arquivo 'credentials_oauth.json' não encontrado.")
                print("Por favor, baixe suas credenciais da API do Google e salve o arquivo neste diretório.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_oauth.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para as próximas execuções.
        with open('token.pickle', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Autenticação com o Gmail realizada com sucesso.")
        return service
    except HttpError as error:
        print(f'Ocorreu um erro durante a autenticação: {error}')
        return None

def criar_email_com_anexo(destinatario, assunto, corpo_texto, caminho_arquivo):
    """
    Cria uma mensagem de e-mail com um anexo, pronta para ser enviada pela API.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo de anexo '{caminho_arquivo}' não foi encontrado.")
        return None

    message = MIMEMultipart()
    message['to'] = destinatario
    message['subject'] = assunto

    # Adiciona o corpo do e-mail
    message.attach(MIMEText(corpo_texto, 'plain'))

    # Processa o anexo
    content_type, encoding = mimetypes.guess_type(caminho_arquivo)
    
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    
    main_type, sub_type = content_type.split('/', 1)
    
    with open(caminho_arquivo, 'rb') as f:
        part = MIMEBase(main_type, sub_type)
        part.set_payload(f.read())
    
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(caminho_arquivo)}"')
    message.attach(part)

    # Codifica a mensagem completa em base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def enviar_email(service, user_id, body):
    """
    Envia o e-mail usando o objeto service da API.
    'user_id' é geralmente 'me' para a conta autenticada.
    'body' é a mensagem codificada em base64.
    """
    try:
        message = service.users().messages().send(userId=user_id, body=body).execute()
        print(f"E-mail enviado com sucesso! ID da Mensagem: {message['id']}")
        return message
    except HttpError as error:
        print(f'Ocorreu um erro ao enviar o e-mail: {error}')
        return None

def main():
    """
    Função principal que orquestra a autenticação, coleta de dados e envio do e-mail.
    """
    service = autenticar_gmail()
    
    if service:
        print("\n--- Preencha os dados para o envio do e-mail ---")
        destinatario = input("Para (destinatário): ")
        assunto = input("Assunto: ")
        corpo = input("Corpo do e-mail: ")
        
        print("\nSelecione o arquivo para anexar...")
        # Usar um file dialog para evitar erros de digitação no caminho do arquivo
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal do tkinter
        caminho_anexo = filedialog.askopenfilename(title="Selecione o anexo")
        
        if not caminho_anexo:
            print("Nenhum arquivo selecionado. O envio foi cancelado.")
            return

        print(f"Arquivo selecionado: {caminho_anexo}")

        email_body = criar_email_com_anexo(destinatario, assunto, corpo, caminho_anexo)
        
        if email_body:
            enviar_email(service, 'me', email_body)

if __name__ == '__main__':
    main()