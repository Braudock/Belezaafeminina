import os
import re
import requests

# It's recommended to load the API key from an environment variable for security
API_KEY = os.environ.get("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def encurtar_nome_com_api(nome_original, max_chars=50):
    """
    Encurta um nome de arquivo usando a API do Google Gemini.
    """
    if not API_KEY:
        print("Erro: A variável de ambiente GEMINI_API_KEY não está definida.")
        # Fallback if API key is not set
        return "".join(filter(str.isalnum, nome_original))[:max_chars]

    prompt = f"Resuma o seguinte nome de arquivo em no máximo 4 palavras, mantendo o significado principal. Retorne apenas o novo nome, sem aspas ou explicações. Nome original: '{nome_original}'"
    
    url = f"{API_URL}?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # Corrected payload for the Gemini API
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        response_data = response.json()
        
        if 'candidates' in response_data and response_data['candidates']:
            content = response_data['candidates'][0].get('content', {})
            parts = content.get('parts', [])
            if parts:
                text_content = parts[0].get('text', '')
                # Limpar o texto para remover aspas e espaços extras
                cleaned_name = text_content.strip().strip('"')
                # Remover caracteres inválidos para nome de arquivo
                cleaned_name = re.sub(r'[<>:"/\\|?*]', '', cleaned_name)
                # Garantir que o nome não exceda o max_chars
                return cleaned_name[:max_chars].strip()
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à API do Gemini: {e}")
    except (KeyError, IndexError) as e:
        print(f"Estrutura de resposta inesperada da API do Gemini: {e}")
    
    # Fallback: se a API falhar, tenta uma abordagem mais simples
    return "".join(filter(str.isalnum, nome_original))[:max_chars]

def renomear_arquivos_em_maiusculas(diretorio):
    """
    Renomeia todos os arquivos em um diretório para maiúsculas,
    encurtando o nome se necessário usando a API do Google Gemini.
    """
    if not os.path.isdir(diretorio):
        print(f"Erro: O diretório '{diretorio}' não existe.")
        return

    for nome_arquivo in os.listdir(diretorio):
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        
        if os.path.isfile(caminho_completo):
            nome_base, extensao = os.path.splitext(nome_arquivo)
            
            # Tenta encurtar o nome usando a API do Gemini
            novo_nome_base = encurtar_nome_com_api(nome_base)
            
            if not novo_nome_base:
                print(f"Pulando: '{nome_arquivo}' (não foi possível gerar um novo nome)")
                continue

            # Converte para maiúsculas e remove caracteres inválidos
            novo_nome_base_maiusculo = re.sub(r'[<>:"/\\|?*]', '', novo_nome_base.upper())
            
            novo_nome_arquivo = novo_nome_base_maiusculo + extensao
            novo_caminho_completo = os.path.join(diretorio, novo_nome_arquivo)
            
            # Evita renomear se o nome for o mesmo (case-insensitive)
            if not os.path.exists(novo_caminho_completo) or os.path.samefile(caminho_completo, novo_caminho_completo):
                try:
                    os.rename(caminho_completo, novo_caminho_completo)
                    print(f"Renomeado: '{nome_arquivo}' para '{novo_nome_arquivo}'")
                except OSError as e:
                    print(f"Erro ao renomear '{nome_arquivo}': {e}")
            else:
                print(f"Pulando: '{nome_arquivo}' (já existe um arquivo com o nome '{novo_nome_arquivo}')")

def main():
    diretorio_alvo = input("Digite o caminho do diretório para renomear os arquivos: ")
    renomear_arquivos_em_maiusculas(diretorio_alvo)

if __name__ == "__main__":
    main()
