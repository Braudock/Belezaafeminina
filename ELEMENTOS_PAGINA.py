import requests
from bs4 import BeautifulSoup
from collections import defaultdict

def analisar_elemento_automatico(tag):
    """Analisa automaticamente o propósito de um elemento"""
    nome = tag.name
    classes = ' '.join(tag.get('class', []))
    id_elem = tag.get('id', '')
    attrs = tag.attrs
    texto = tag.get_text(strip=True)[:100]
    
    # Análise automática baseada em contexto
    proposito = []
    
    # Análise por atributos
    if 'href' in attrs:
        if 'mailto:' in attrs['href']:
            proposito.append("Link de email")
        elif 'tel:' in attrs['href']:
            proposito.append("Link de telefone")
        elif attrs['href'].startswith('#'):
            proposito.append("Link âncora (navegação interna)")
        else:
            proposito.append("Link para página/site")
    
    if 'src' in attrs:
        if nome == 'img':
            if 'logo' in str(attrs.get('src', '')).lower():
                proposito.append("Logo/marca")
            elif 'icon' in str(attrs.get('src', '')).lower():
                proposito.append("Ícone")
            else:
                proposito.append("Imagem de conteúdo")
        elif nome == 'script':
            proposito.append("Script externo")
    
    # Análise por classes e IDs
    identificadores = (classes + ' ' + id_elem).lower()
    
    if any(x in identificadores for x in ['nav', 'menu', 'navbar']):
        proposito.append("Navegação/Menu")
    elif any(x in identificadores for x in ['header', 'topo', 'top']):
        proposito.append("Cabeçalho")
    elif any(x in identificadores for x in ['footer', 'rodape', 'bottom']):
        proposito.append("Rodapé")
    elif any(x in identificadores for x in ['sidebar', 'lateral', 'aside']):
        proposito.append("Barra lateral")
    elif any(x in identificadores for x in ['content', 'main', 'principal']):
        proposito.append("Conteúdo principal")
    elif any(x in identificadores for x in ['ad', 'banner', 'publicidade']):
        proposito.append("Publicidade")
    elif any(x in identificadores for x in ['search', 'busca', 'pesquisa']):
        proposito.append("Busca")
    elif any(x in identificadores for x in ['social', 'share', 'compartilhar']):
        proposito.append("Redes sociais")
    elif any(x in identificadores for x in ['video', 'player']):
        proposito.append("Player de vídeo")
    elif any(x in identificadores for x in ['form', 'formulario']):
        proposito.append("Formulário")
    elif any(x in identificadores for x in ['button', 'btn']):
        proposito.append("Botão de ação")
    elif any(x in identificadores for x in ['title', 'titulo', 'heading']):
        proposito.append("Título")
    elif any(x in identificadores for x in ['date', 'data', 'time']):
        proposito.append("Data/hora")
    elif any(x in identificadores for x in ['author', 'autor']):
        proposito.append("Autor")
    
    # Análise por conteúdo
    if texto:
        if any(x in texto.lower() for x in ['copyright', '©', 'todos os direitos']):
            proposito.append("Copyright")
        elif '@' in texto and '.' in texto:
            proposito.append("Contato/email")
        elif texto.startswith(('R$', '$', '€')):
            proposito.append("Preço/valor")
    
    # Análise por tipo de elemento
    if nome == 'meta':
        if attrs.get('property', '').startswith('og:'):
            proposito.append("Open Graph (compartilhamento social)")
        elif attrs.get('name') == 'description':
            proposito.append("Descrição da página")
        elif attrs.get('name') == 'keywords':
            proposito.append("Palavras-chave SEO")
    
    return proposito if proposito else ["Elemento de estrutura/estilização"]

def descobrir_elementos(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    elementos_analisados = defaultdict(lambda: defaultdict(int))
    
    print(f"ANÁLISE AUTOMÁTICA DE {url}\n" + "="*60)
    
    # Analisar cada elemento
    for tag in soup.find_all():
        propositos = analisar_elemento_automatico(tag)
        for proposito in propositos:
            elementos_analisados[tag.name][proposito] += 1
    
    # Exibir resultados
    for elemento, propositos in sorted(elementos_analisados.items()):
        total = sum(propositos.values())
        print(f"\n{elemento.upper()} ({total} ocorrências)")
        
        for proposito, qtd in sorted(propositos.items(), key=lambda x: x[1], reverse=True):
            porcentagem = (qtd/total) * 100
            print(f"  → {proposito}: {qtd}x ({porcentagem:.1f}%)")

# Executar - não precisa configurar nada!
descobrir_elementos('https://www.uol.com.br/')