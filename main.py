import os
import subprocess
from datetime import datetime
from imap_tools import MailBox, AND
# Importa as credenciais do seu arquivo secrets.py
from secrets import EMAIL, SENHA

# --- CONFIGURAÇÕES ---
PASTA_DESTINO = "data-raw"
ASSUNTO_BUSCA = "extracao" # O script só baixará emails com essa palavra no assunto

def git_push_automatico(nome_arquivo):
    """Função para enviar pro GitHub automaticamente"""
    try:
        print("--- Iniciando Git Push ---")
        # Adiciona o arquivo específico
        subprocess.run(["git", "add", nome_arquivo], check=True)
        
        # Cria o commit com data e hora
        msg = f"Auto: Adiciona dados {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        
        # Envia para o repositório
        subprocess.run(["git", "push"], check=True)
        print("🚀 Sucesso! Arquivo enviado para o GitHub.")
    except Exception as e:
        print(f"⚠️ Erro no Git: {e}")

def main():
    # Cria a pasta se não existir
    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)

    print(f"--- Buscando e-mail com assunto: '{ASSUNTO_BUSCA}' ---")
    
    try:
        # Conecta no Gmail
        with MailBox('imap.gmail.com').login(EMAIL, SENHA) as mailbox:
            
            # Busca emails NÃO lidos (seen=False) ou remova esse filtro para todos
            criterios = AND(subject=ASSUNTO_BUSCA)
            
            # Pega o último email encontrado
            for msg in mailbox.fetch(criterios, limit=1, reverse=True):
                print(f"Processando email: {msg.subject}")
                
                encontrou_csv = False
                for att in msg.attachments:
                    if att.filename.lower().endswith('.csv'):
                        caminho_final = os.path.join(PASTA_DESTINO, att.filename)
                        
                        with open(caminho_final, 'wb') as f:
                            f.write(att.payload)
                        
                        print(f"✅ Arquivo salvo: {caminho_final}")
                        
                        # Chama a função de Git
                        git_push_automatico(caminho_final)
                        encontrou_csv = True
                
                if not encontrou_csv:
                    print("Email encontrado, mas sem anexo CSV.")

    except Exception as e:
        print(f"❌ Erro de conexão ou autenticação: {e}")

if __name__ == "__main__":
    main()