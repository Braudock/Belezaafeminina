#!/usr/bin/env python3
"""
Script para auxiliar na recuperação de celular hackeado/clonado
Automatiza verificações e organiza o processo de recuperação
"""

import os
import json
import datetime
import time
import subprocess
import requests
from typing import Dict, List

class CelularRecovery:
    def __init__(self, numero_linha: str):
        self.numero = numero_linha
        self.log_file = f"recovery_log_{numero_linha}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.recovery_data = {
            "numero": numero_linha,
            "inicio_processo": datetime.datetime.now().isoformat(),
            "acoes_realizadas": [],
            "contatos_importantes": {},
            "status": "iniciado"
        }
    
    def log_acao(self, acao: str, detalhes: str = ""):
        """Registra ação realizada no log"""
        timestamp = datetime.datetime.now().isoformat()
        self.recovery_data["acoes_realizadas"].append({
            "timestamp": timestamp,
            "acao": acao,
            "detalhes": detalhes
        })
        print(f"[{timestamp}] ✓ {acao}")
        if detalhes:
            print(f"    → {detalhes}")
    
    def verificar_status_linha(self):
        """Verifica se a linha ainda responde"""
        print("\n🔍 VERIFICANDO STATUS DA LINHA")
        try:
            # Simulação de ping para verificar conectividade
            response = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                    capture_output=True, text=True, timeout=5)
            if response.returncode == 0:
                self.log_acao("Internet funcionando", "Conexão OK para próximos passos")
            else:
                self.log_acao("Sem internet", "Verificar conexão Wi-Fi")
        except Exception as e:
            self.log_acao("Erro verificação", f"Erro: {str(e)}")
    
    def gerar_checklist_emergencia(self):
        """Gera checklist de ações imediatas"""
        print("\n🚨 CHECKLIST DE EMERGÊNCIA")
        checklist = [
            "1. Ligar AGORA para 1056 (TIM) e reportar hack",
            "2. Solicitar bloqueio imediato da linha",
            "3. Ir pessoalmente a loja TIM com RG e CPF",
            "4. Solicitar novo chip com mesmo número",
            "5. Alterar senhas de apps (WhatsApp, bancos)",
            "6. Ativar 2FA onde possível",
            "7. Verificar movimentações bancárias",
            "8. Registrar B.O. online se necessário",
            "9. Notificar contatos importantes sobre hack",
            "10. Monitorar contas por 48h"
        ]
        
        for item in checklist:
            print(f"  {item}")
        
        self.log_acao("Checklist gerado", "10 ações prioritárias listadas")
        return checklist
    
    def gerar_template_contatos(self):
        """Gera template de mensagem para avisar contatos"""
        template = f"""
🚨 AVISO DE SEGURANÇA 🚨

Meu número {self.numero} foi hackeado/clonado.

❌ NÃO aceitem pedidos de dinheiro
❌ NÃO enviem códigos ou senhas
❌ NÃO façam transferências

✅ Para falar comigo, me liguem ou mandem WhatsApp
✅ Confirmen pedidos pessoalmente

Estou resolvendo com a operadora.
Obrigado!
"""
        print("\n📱 TEMPLATE PARA AVISAR CONTATOS:")
        print(template)
        self.log_acao("Template criado", "Mensagem para avisar contatos")
        return template
    
    def verificar_apps_vulneraveis(self):
        """Lista apps que usam número para autenticação"""
        print("\n🔐 APPS QUE PRECISAM ATENÇÃO:")
        apps_criticos = [
            "WhatsApp - Alterar autenticação em duas etapas",
            "Instagram - Verificar logins ativos",
            "Facebook - Revisar dispositivos conectados", 
            "Bancos (Itaú, Bradesco, etc) - Alterar senhas",
            "Uber/99 - Verificar viagens não autorizadas",
            "iFood - Verificar pedidos suspeitos",
            "Email - Ativar 2FA",
            "Telegram - Verificar sessões ativas"
        ]
        
        for app in apps_criticos:
            print(f"  ⚠️  {app}")
        
        self.log_acao("Apps vulneráveis listados", f"{len(apps_criticos)} apps identificados")
        return apps_criticos
    
    def monitorar_recuperacao(self, intervalo_minutos: int = 30):
        """Monitora o processo de recuperação"""
        print(f"\n⏰ INICIANDO MONITORAMENTO (verificação a cada {intervalo_minutos}min)")
        
        tentativas = 0
        max_tentativas = 48  # 24h se intervalo = 30min
        
        while tentativas < max_tentativas:
            try:
                # Simula verificação de status
                print(f"\n🔄 Verificação #{tentativas + 1}")
                
                # Aqui você pode adicionar verificações reais:
                # - Ping para número
                # - Verificação de apps
                # - Status de notificações
                
                resposta = input("Linha já foi recuperada? (s/n): ").lower()
                if resposta == 's':
                    self.log_acao("LINHA RECUPERADA", "Processo concluído com sucesso!")
                    self.recovery_data["status"] = "recuperado"
                    self.salvar_log()
                    return True
                
                tentativas += 1
                if tentativas < max_tentativas:
                    print(f"⏳ Aguardando {intervalo_minutos} minutos...")
                    time.sleep(intervalo_minutos * 60)
                    
            except KeyboardInterrupt:
                print("\n⏹️  Monitoramento interrompido pelo usuário")
                break
        
        print("⚠️  Tempo limite de monitoramento atingido")
        return False
    
    def salvar_log(self):
        """Salva log completo do processo"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.recovery_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Log salvo em: {self.log_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar log: {e}")
    
    def executar_processo_completo(self):
        """Executa o processo completo de recuperação"""
        print("="*60)
        print("🔥 SCRIPT DE RECUPERAÇÃO DE CELULAR HACKEADO")
        print("="*60)
        print(f"📱 Número: {self.numero}")
        print(f"⏰ Início: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Executa todas as etapas
        self.verificar_status_linha()
        self.gerar_checklist_emergencia()
        self.gerar_template_contatos() 
        self.verificar_apps_vulneraveis()
        
        print("\n" + "="*60)
        print("🎯 PRÓXIMOS PASSOS CRÍTICOS:")
        print("1. LIGUE AGORA: 1056 (TIM)")
        print("2. VÁ À LOJA TIM com RG e CPF")
        print("3. TROQUE TODAS AS SENHAS")
        print("="*60)
        
        # Pergunta se quer monitorar
        monitor = input("\nIniciar monitoramento automático? (s/n): ").lower()
        if monitor == 's':
            while True:
                try:
                    intervalo_input = input("Intervalo em minutos (padrão 30): ").strip()
                    if not intervalo_input:
                        intervalo = 30
                        break
                    elif intervalo_input.isdigit() and int(intervalo_input) > 0:
                        intervalo = int(intervalo_input)
                        break
                    else:
                        print("❌ Digite apenas números positivos ou ENTER para padrão")
                except ValueError:
                    print("❌ Entrada inválida, tente novamente")
            
            print(f"✅ Usando intervalo de {intervalo} minutos")
            self.monitorar_recuperacao(intervalo)
        
        self.recovery_data["fim_processo"] = datetime.datetime.now().isoformat()
        self.salvar_log()
        
        print("\n✅ Processo concluído! Verifique o arquivo de log gerado.")

def main():
    """Função principal"""
    print("🔥 RECUPERAÇÃO DE CELULAR HACKEADO")
    print("Desenvolvido para casos de urgência\n")
    
    # Solicita número
    numero = input("Digite seu número (ex: 11983083306): ").strip()
    if not numero:
        print("❌ Número obrigatório!")
        return
    
    # Confirma antes de prosseguir
    print(f"\n📱 Número: {numero}")
    confirmacao = input("Confirmar e iniciar processo? (s/n): ").lower()
    
    if confirmacao != 's':
        print("❌ Processo cancelado pelo usuário")
        return
    
    # Executa recuperação
    recovery = CelularRecovery(numero)
    recovery.executar_processo_completo()

if __name__ == "__main__":
    main()