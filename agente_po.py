import os
import logging
import ollama
from jira import JIRA
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")

load_dotenv()

jira = JIRA(
    server=os.getenv("JIRA_SERVER"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))
)

PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")

# -------------------------
# PROMPT INTELIGENTE QA
# -------------------------
def gerar_prompt_qa(story):
    return f"""
Você é um QA Analista Sênior AUTÔNOMO especialista em ERP.

Sua missão é analisar a história e extrair APENAS o essencial para testes.

STORY:
{story}

REGRAS DE PENSAMENTO:

1. Foque no que QUEBRA o sistema
2. Ignore layout, cor e estética
3. Priorize:
   - validação obrigatória
   - fluxo principal
   - erros críticos
   - impacto no negócio

4. Gere apenas:

### 🔥 RISCOS CRÍTICOS
Liste os principais riscos do sistema

### 🎯 CENÁRIOS ESSENCIAIS (Gherkin)
Somente os mais importantes

Formato:
Dado / Quando / Então

### ⚠️ POSSÍVEIS FALHAS
Liste bugs prováveis

### 🚀 ESTRATÉGIA DE TESTE
Explique como testar de forma inteligente

REGRAS:
- Seja direto
- Não encha de cenário inútil
- Pense como QA experiente
"""

# -------------------------
# EXECUTOR QA
# -------------------------
def analisar_stories():
    logging.info("🧠 [QA ANALISTA] Analisando histórias...")

    issues = jira.search_issues(
        f'project="{PROJECT_KEY}" AND status="To Do"',
        maxResults=10
    )

    for issue in issues:

        logging.info(f"🔎 Analisando {issue.key}")

        # evita duplicar análise
        comentarios = jira.comments(issue)
        if any("RISCOS CRÍTICOS" in c.body for c in comentarios):
            logging.info("⏭️ Já analisado, pulando...")
            continue

        prompt = gerar_prompt_qa(issue.fields.description)

        try:
            res = ollama.chat(
                model='llama3',
                messages=[{'role': 'user', 'content': prompt}]
            )

            analise = res['message']['content']

            jira.add_comment(issue, analise)

            # tenta mover status
            try:
                jira.transition_issue(issue, "In Progress")
            except:
                logging.warning("⚠️ Não conseguiu mudar status")

            logging.info(f"✅ QA analisou {issue.key}")

        except Exception as e:
            logging.error(f"❌ Erro QA: {e}")

# -------------------------
# LOOP
# -------------------------
if __name__ == "__main__":
    while True:
        try:
            analisar_stories()
        except Exception as e:
            logging.error(f"Erro geral: {e}")

        import time
        time.sleep(30)