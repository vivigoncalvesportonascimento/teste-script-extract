import os
import subprocess
from datetime import date, datetime
from imap_tools import MailBox, AND
from secrets import EMAIL, SENHA

# --- CONFIGURAÇÕES ---
PASTA_DESTINO = "data-raw"

# DICIONÁRIO DE ARQUIVOS
# Chave (Esquerda): O texto que buscamos no ASSUNTO do e-mail
# Valor (Direita): O nome fixo que o arquivo terá no computador (sem data)
MAPA_ARQUIVOS = {
    "dados-armazem-siafi-execucao-siafi-12": "dados-armazem-siafi-execucao-siafi-12.csv",
    "dados-armazem-siafi-credito-inicial-autorizado": "dados-armazem-siafi-credito-inicial-autorizado.csv",
    "dados-armazem-siafi-cota-item-data": "dados-armazem-siafi-cota-item-data.csv"
}


def git_push_geral():
    """Envia todas as mudanças da pasta data-raw de uma vez"""
    try:
        print("\n--- 2. Iniciando Sincronização com GitHub ---")
        # Atualiza antes de enviar
        subprocess.run(["git", "pull"], check=False)
        subprocess.run(["git", "add", "data-raw/"], check=True)

        # Commit com timestamp para controle de versão
        msg = f"Auto: Carga diaria {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)

        subprocess.run(["git", "push"], check=True)
        print("🚀 Sucesso! Todos os arquivos foram atualizados no GitHub.")
    except subprocess.CalledProcessError:
        print("⚠️ Nada novo para enviar ou erro no Git.")
    except Exception as e:
        print(f"❌ Erro genérico no Git: {e}")


def main():
    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)

    # Variável para controlar se TUDO deu certo hoje
    arquivos_baixados_hoje = 0
    total_esperado = len(MAPA_ARQUIVOS)

    # Data de hoje para filtro (ex: 2026-01-15)
    hoje = date.today()

    print(f"--- 1. Iniciando busca para data: {hoje.strftime('%d/%m/%Y')} ---")

    try:
        with MailBox('imap.gmail.com').login(EMAIL, SENHA) as mailbox:

            # Loop pelos itens do nosso dicionário
            for assunto_busca, nome_final in MAPA_ARQUIVOS.items():
                print(f"\n🔍 Procurando relatório: '{assunto_busca}'...")

                # CRITÉRIO: Assunto específico E Data de hoje
                criterios = AND(subject=assunto_busca, date=hoje)

                # Pega apenas 1 email (o mais recente de hoje, se houver duplicidade)
                msgs = list(mailbox.fetch(criterios, limit=1, reverse=True))

                if not msgs:
                    # MENSAGEM DE ERRO SOLICITADA
                    print(
                        f"❌ Erro: consulta não encontrada para '{assunto_busca}' na data de hoje.")
                    continue

                for msg in msgs:
                    print(f"   📧 E-mail localizado: '{msg.subject}'")

                    anexo_encontrado = False
                    for att in msg.attachments:
                        # Verifica se é CSV
                        if att.filename.lower().endswith('.csv'):

                            # AQUI A MÁGICA: Salvamos com o nome fixo (sem a data do anexo original)
                            caminho_final = os.path.join(
                                PASTA_DESTINO, nome_final)

                            with open(caminho_final, 'wb') as f:
                                f.write(att.payload)

                            print(f"   ✅ Arquivo salvo como: {nome_final}")
                            anexo_encontrado = True
                            arquivos_baixados_hoje += 1
                            break  # Para de olhar outros anexos deste email

                    if not anexo_encontrado:
                        print("   ⚠️ E-mail encontrado, mas sem anexo CSV válido.")

    except Exception as e:
        print(f"❌ Erro crítico de conexão: {e}")
        return

    # Lógica Final: Só faz o push se baixou algo, mas avisa se faltou algo
    print("\n------------------------------------------------")
    print(
        f"Resumo: {arquivos_baixados_hoje} de {total_esperado} arquivos baixados.")

    if arquivos_baixados_hoje == 0:
        print("❌ ERRO: Nenhuma consulta do dia foi encontrada. Nada será enviado.")
    else:
        # Se baixou pelo menos um, enviamos.
        # (Se quiser ser rigorosa e só enviar se baixar TODOS, mude o if para: if arquivos_baixados_hoje == total_esperado:)
        git_push_geral()


if __name__ == "__main__":
    main()
