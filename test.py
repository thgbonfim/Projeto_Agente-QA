import os
import time
import logging
from typing import Callable, Tuple
from dotenv import load_dotenv
from jira import JIRA
from groq import Groq

# ==============================
# 🔐 CONFIGURAÇÕES E ENV
# ==============================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)

JIRA_SERVER = os.getenv("JIRA_SERVER", "").strip()
USER_EMAIL = os.getenv("JIRA_EMAIL", "").strip()
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# ==============================
# 🎯 REGRA DE BUSCA (JQL)
# ==============================
# Usamos o operador ~ (contém) para ignorar diferenças exatas de nome
# Ele vai pegar qualquer card do projeto KAN que esteja em uma coluna com a palavra "Teste"
JQL_QUERY = 'project = "KAN" AND status = "To Do" ORDER BY created DESC'
# ==============================
# 🔁 MECANISMO DE RETRY
# ==============================
def retry_request(func: Callable, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait_time = (2 ** attempt) * 15
                logging.warning(f"⚠️ Rate limit Groq. Aguardando {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("❌ Falha crítica de cota na Groq.")

# ==============================
# 📡 INTEGRAÇÃO JIRA
# ==============================
def conectar_jira() -> JIRA:
    try:
        return JIRA(server=JIRA_SERVER, basic_auth=(USER_EMAIL, JIRA_TOKEN))
    except Exception as e:
        logging.error(f"❌ Erro de conexão Jira: {e}")
        exit(1)

def ja_foi_analisado(jira: JIRA, issue) -> bool:
    """Verifica se o bot já comentou nesta issue para evitar spam."""
    comentarios = jira.comments(issue)
    for c in comentarios:
        if "AGENTE ANALISTA" in c.body or "CASOS DE TESTE" in c.body:
            return True
    return False

# ==============================
# 🧠 IA: GERAÇÃO DE TESTES
# ==============================
def gerar_testes(titulo: str, descricao: str) -> str:
    prompt = f"""
Atue como um QA Sênior. 
Com base na História abaixo, gere APENAS os Casos de Teste necessários (Caminho Feliz, Exceções e Casos de Borda).
NÃO escreva introduções ou explicações. Retorne estritamente a lista formatada.

História: {titulo}
Descrição: {descricao}

Formato obrigatório:
- CT01: [Título do Teste]
  - Pré-condição: ...
  - Passos: ...
  - Resultado Esperado: ...
"""
    client = Groq(api_key=GROQ_API_KEY)
    
    def request_groq():
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    
    return retry_request(request_groq)

# ==============================
# 🚀 ORQUESTRADOR DE FILA
# ==============================
def processar_fila():
    logging.info("🤖 Iniciando Agente Autônomo QA...")
    jira = conectar_jira()
    
    logging.info(f"🔍 Buscando fila com JQL: [{JQL_QUERY}]")
    try:
        issues_na_fila = jira.search_issues(JQL_QUERY, maxResults=15)
    except Exception as e:
        logging.error(f"❌ Erro na busca JQL: {e}")
        return

    if not issues_na_fila:
        logging.info("💤 Nenhuma história nova na fila no momento.")
        return

    logging.info(f"📦 {len(issues_na_fila)} histórias encontradas. Processando...")

    for issue in issues_na_fila:
        logging.info(f"\n{'-'*40}\n▶️ AVALIANDO: {issue.key} - {issue.fields.summary}\n{'-'*40}")
        
        if ja_foi_analisado(jira, issue):
            logging.info(f"⏭️ {issue.key} já possui testes gerados. Pulando...")
            continue
            
        try:
            titulo = issue.fields.summary
            descricao = issue.fields.description or "Sem descrição fornecida."
            
            logging.info("🧠 Gerando casos de teste via IA...")
            testes = gerar_testes(titulo, descricao)
            
            comentario = f"🤖 **CASOS DE TESTE AUTOMATIZADOS (AGENTE ANALISTA)**\n\n{testes}"
            jira.add_comment(issue.id, comentario)
            logging.info(f"✅ Testes postados com sucesso na {issue.key}")
            
            time.sleep(3) 
            
        except Exception as e:
            logging.error(f"❌ Erro ao processar {issue.key}: {e}")
            continue 

    logging.info("\n🏁 CICLO FINALIZADO.")

# ==============================
# 🕵️ MODO VIGILANTE (LOOP)
# ==============================
if __name__ == "__main__":
    INTERVALO_SEGUNDOS = 300 
    
    logging.info(f"🚀 MODO VIGILANTE ATIVADO (Verificação a cada {INTERVALO_SEGUNDOS}s)")
    logging.info("Pressione CTRL+C para parar o agente.")

    while True:
        try:
            processar_fila()
            logging.info(f"💤 Ciclo concluído. Próxima ronda em {INTERVALO_SEGUNDOS}s...")
            time.sleep(INTERVALO_SEGUNDOS)
            
        except KeyboardInterrupt:
            logging.info("\n🛑 Agente parado pelo utilizador.")
            break
        except Exception as e:
            logging.error(f"⚠️ Erro inesperado no ciclo: {e}")
            time.sleep(INTERVALO_SEGUNDOS)