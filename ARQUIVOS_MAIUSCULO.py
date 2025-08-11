import os
import requests
import re
from pathlib import Path

def encurtar_nome_com_api(nome_original, max_chars=25):
    """Usa API do Google Gemini para criar nome mais curto e inteligente"""
    
    # Sua chave da API Google Gemini
    api_key = "AIzaSyDDMS6mnkgwXJHsZJBnetMZ6tu_NuPvGgc"
    
    if len(nome_original) <= max_chars:
        return nome_original
    
    # URL corrigida para usar modelo gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""Crie uma versão curta (máximo {max_chars} caracteres) do nome de arquivo: "{nome_original}"

Regras:
- Mantenha apenas palavras-chave importantes
- Use abreviações inteligentes  
- Sem espaços ou caracteres especiais
- APENAS o nome encurtado, sem explicações"""
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 50
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            resultado = response.json()
            
            if 'candidates' in resultado and len(resultado['candidates']) > 0:
                nome_curto = resultado['candidates'][0]['content']['parts'][0]['text'].strip()
                # Remove caracteres especiais e garante tamanho máximo
                nome_curto = re.sub(r'[^A-Za-z0-9_]', '', nome_curto)[:max_chars]
                return nome_curto if nome_curto else nome_original[:max_chars]
            else:
                print("Resposta vazia da API")
                return nome_original[:max_chars]
        else:
            print(f"Erro na API Google: {response.status_code}")
            return nome_original[:max_chars]
            
    except Exception as e:
        print(f"Erro ao chamar API Google: {e}")
        return nome_original[:max_chars]

def encurtar_nome_local(nome_original, max_chars=25):
    """Alternativa local sem API - remove palavras comuns e abrevia"""
    
    if len(nome_original) <= max_chars:
        return nome_original
    
    # Palavras comuns para remover
    palavras_remover = ['THE', 'AND', 'OR', 'BUT', 'IN', 'ON', 'AT', 'TO', 'FOR', 
                       'OF', 'WITH', 'BY', 'A', 'AN', 'IS', 'ARE', 'WAS', 'WERE',
                       'DOCUMENTO', 'ARQUIVO', 'RELATORIO', 'PLANILHA']
    
    # Divide em palavras
    palavras = nome_original.upper().split('_')
    
    # Remove palavras comuns
    palavras_filtradas = [p for p in palavras if p not in palavras_remover]
    
    # Se não sobrou nada, mantém palavras originais
    if not palavras_filtradas:
        palavras_filtradas = palavras
    
    # Tenta abreviar palavras longas
    palavras_abreviadas = []
    for palavra in palavras_filtradas:
        if len(palavra) > 8:
            # Pega primeiras 4 + últimas 2 letras
            palavra = palavra[:4] + palavra[-2:]
        palavras_abreviadas.append(palavra)
    
    nome_resultado = '_'.join(palavras_abreviadas)
    
    # Se ainda estiver longo, trunca
    if len(nome_resultado) > max_chars:
        nome_resultado = nome_resultado[:max_chars]
    
    return nome_resultado

def renomear_arquivos_pdf():
    # Caminho da pasta
    pasta = r"C:\Users\BRAUD\Desktop\PDF"
    
    # Verifica se a pasta existe
    if not os.path.exists(pasta):
        print(f"Pasta não encontrada: {pasta}")
        return
    
    print("Escolha o método de encurtamento:")
    print("1 - API OpenAI (mais inteligente)")
    print("2 - Método local (sem internet)")
    escolha = input("Digite 1 ou 2: ")
    
    usar_api = escolha == "1"
    
    # Lista todos os arquivos na pasta
    for arquivo in os.listdir(pasta):
        caminho_completo = os.path.join(pasta, arquivo)
        
        # Verifica se é um arquivo (não pasta)
        if os.path.isfile(caminho_completo):
            # Separa nome e extensão
            nome, extensao = os.path.splitext(arquivo)
            
            # Aplica transformações no nome
            nome_processado = nome.upper().replace(" ", "_")
            
            # Encurta o nome usando API ou método local
            if usar_api:
                nome_curto = encurtar_nome_com_api(nome_processado)
            else:
                nome_curto = encurtar_nome_local(nome_processado)
            
            # Reconstrói o nome completo com extensão
            novo_arquivo = nome_curto + extensao
            novo_caminho = os.path.join(pasta, novo_arquivo)
            
            # Verifica se arquivo já existe e adiciona contador se necessário
            contador = 1
            while os.path.exists(novo_caminho) and novo_arquivo != arquivo:
                nome_com_contador = f"{nome_curto}_{contador}{extensao}"
                novo_caminho = os.path.join(pasta, nome_com_contador)
                novo_arquivo = nome_com_contador
                contador += 1
            
            # Renomeia apenas se o nome mudou
            if arquivo != novo_arquivo:
                try:
                    os.rename(caminho_completo, novo_caminho)
                    print(f"Renomeado: {arquivo}")
                    print(f"    Para: {novo_arquivo}")
                    print()
                except OSError as e:
                    print(f"Erro ao renomear {arquivo}: {e}")
            else:
                print(f"Sem alteração: {arquivo}")

# Executa a função
if __name__ == "__main__":
    renomear_arquivos_pdf()
    print("\nProcesso concluído!")