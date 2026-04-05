import shutil
import os
import time
import logging
import subprocess
from dotenv import load_dotenv
from jira import JIRA
from groq import Groq

# ==============================
# 🔐 CONFIGURAÇÕES E AMBIENTE
# ==============================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")

def limpar_env(valor): 
    return valor.strip() if valor else ""

JIRA_SERVER = limpar_env(os.getenv("JIRA_SERVER"))
USER_EMAIL = limpar_env(os.getenv("JIRA_EMAIL"))
JIRA_TOKEN = limpar_env(os.getenv("JIRA_TOKEN"))
GROQ_API_KEY = limpar_env(os.getenv("GROQ_API_KEY"))

groq_client = Groq(api_key=GROQ_API_KEY)

def conectar_jira():
    return JIRA(server=JIRA_SERVER, basic_auth=(USER_EMAIL, JIRA_TOKEN))

# ==============================
# 📡 LEITURA DE CENÁRIOS (SEM IGNORAR)
# ==============================
def obter_cenarios(issue):
    # 1. Pega a descrição
    descricao = issue.fields.description or ""
    
    # 2. Pega todos os comentários (limpando o que é do robô)
    comentarios_humanos = [
        c.body for c in issue.fields.comment.comments 
        if "Automação" not in c.body and "✅" not in c.body and "❌" not in c.body
    ]
    
    # 3. Junta tudo
    texto_total = descricao + "\n" + "\n".join(comentarios_humanos)
    
    # 4. Se o texto tiver MAIS de 20 caracteres, vamos tentar processar 
    # (Removi a trava obrigatória de palavras-chave para testar o KAN-1 e KAN-3)
    if len(texto_total.strip()) > 20:
        logging.info(f"✅ Texto identificado em {issue.key}, enviando para a IA analisar...")
        return texto_total
    
    logging.warning(f"⚠️ {issue.key} ignorado: Card parece estar vazio.")
    return None
    descricao = issue.fields.description or ""
    # Filtra comentários: ignora os do próprio robô para não ler erros antigos como cenário
    comentarios_humanos = [
        c.body for c in issue.fields.comment.comments 
        if "Automação" not in c.body and "✅" not in c.body and "❌" not in c.body
    ]
    
    texto_total = descricao + "\n" + "\n".join(comentarios_humanos)
    texto_lower = texto_total.lower()
    
    # Busca por padrões de teste para não ignorar o card
    padroes = ["ct-", "cenário", "cenario", "test case", "it(", "describe("]
    if any(key in texto_lower for key in padroes):
        logging.info(f"✅ Cenários identificados em {issue.key}")
        return texto_total
    
    logging.warning(f"⚠️ {issue.key} ignorado: Nenhum cenário encontrado.")
    return None

# ==============================
# 🧠 IA: GERADOR DE CÓDIGO
# ==============================
def gerar_codigo_cypress(cenarios, issue_key):
    prompt = f"""
    Gere um script Cypress para a Issue {issue_key}.
    CENÁRIOS: {cenarios}
    URL: https://demoqa.com/automation-practice-form

    REGRAS CRÍTICAS:
    1. BEFORE-EACH: Remova #fixedban e footer com cy.get(...).invoke('remove').
    2. CLIQUES: Use {{force: true}} para rádio e checkbox.
    3. VALIDAÇÃO DE ERRO: O site usa borda vermelha (rgb(220, 53, 69)).
    4. OUTPUT: Apenas código JS puro, começando com describe.
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "system", "content": "QA Sênior. Responda apenas com código JS puro."},
                      {"role": "user", "content": prompt}], 
            temperature=0.1
        )
        codigo = response.choices[0].message.content
        codigo = codigo.replace("```javascript", "").replace("```js", "").replace("```", "").strip()
        return codigo[codigo.find("describe"):] if "describe" in codigo else codigo
    except Exception as e:
        logging.error(f"❌ Erro IA: {e}")
        return ""

# ==============================
# ⚙️ EXECUÇÃO E LÓGICA DA FLAG (BANDEIRA)
# ==============================
def rodar_cypress(issue_key):
    logging.info(f"🚀 Rodando Cypress para {issue_key}...")
    report_dir = "cypress/reports"
    if os.path.exists(report_dir):
        try: shutil.rmtree(report_dir)
        except: pass

    comando = f'npx cypress run --spec "cypress/e2e/{issue_key}.cy.js" --config defaultCommandTimeout=5000'
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
    return resultado.stdout

def anexar_evidencias(jira, issue, log):
    caminho_html = "cypress/reports/mochawesome.html"
    
    # Aguarda o arquivo ser gerado
    for _ in range(15):
        if os.path.exists(caminho_html) and os.path.getsize(caminho_html) > 5000:
            break
        time.sleep(1)

    if os.path.exists(caminho_html):
        with open(caminho_html, "rb") as f:
            jira.add_attachment(issue=issue, attachment=f)
        logging.info(f"📊 Relatório anexado ao card {issue.key}")

    log_l = log.lower()
    # Verifica sucesso: 0 falhas e pelo menos 1 teste passado
    passou_tudo = "failing: 0" in log_l and ("passing: 1" in log_l or "passing: 2" in log_l or "passing: 3" in log_l)

    # ID padrão da Bandeira de Impedimento no Jira Cloud
    FIELD_FLAG = 'customfield_10021' 

    if passou_tudo:
        try:
            # ✅ SUCESSO: Remove a Bandeira Amarela e finaliza
            issue.update(fields={FIELD_FLAG: None})
            jira.transition_issue(issue, transition='Done')
            jira.add_comment(issue.id, "✅ **Automação OK:** Testes passaram e a flag de impedimento foi removida.")
            logging.info(f"🏆 {issue.key} finalizado com sucesso!")
        except Exception as e:
            logging.error(f"❌ Erro ao processar sucesso: {e}")
    else:
        try:
            # 🚩 FALHA: Ativa a Bandeira Amarela (Impediment)
            issue.update(fields={FIELD_FLAG: [{'value': 'Impediment'}]})
            jira.add_comment(issue.id, "❌ **FALHA:** O teste falhou. O card foi marcado com a Flag de impedimento.")
            logging.warning(f"🚩 {issue.key} marcado com FLAG de impedimento.")
        except Exception as e:
            logging.error(f"❌ Erro ao aplicar Flag: {e}")

# ==============================
# 🚀 MOTOR DE VIGILÂNCIA
# ==============================
def vigiar_jira():
    os.makedirs("cypress/e2e", exist_ok=True)
    jira = conectar_jira()
    logging.info("🤖 Agente QA Vigilante Online...")
    
    while True:
        try:
            issues = jira.search_issues('project=KAN AND status="Ready for Test"')
            if issues:
                issue = issues[0] # Processa um por um para não bagunçar
                logging.info(f"⚡ Iniciando: {issue.key}")

                try: jira.transition_issue(issue, transition='Testing')
                except: pass

                cenarios = obter_cenarios(issue)
                if cenarios:
                    codigo = gerar_codigo_cypress(cenarios, issue.key)
                    if codigo:
                        with open(f"cypress/e2e/{issue.key}.cy.js", "w", encoding="utf-8") as f:
                            f.write(codigo)
                        log_exec = rodar_cypress(issue.key)
                        anexar_evidencias(jira, issue, log_exec)
                
                logging.info(f"🏁 Fim do ciclo para {issue.key}")
            else:
                logging.info("💤 Aguardando novos cards...")
        except Exception as e:
            logging.error(f"💥 Erro motor: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    vigiar_jira()