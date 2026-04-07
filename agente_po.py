import os
import ollama
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))

def gerar_story_local():
    print("🧠 [P.O. LOCAL] Gerando requisitos via Ollama...")
    
    prompt = """
    Você é um P.O. Senior. Crie uma Story para: 'Cadastro de Duplicatas'.
    REGRAS: 
    1. Use IDs: #input-razao-social, #input-cnpj, #input-valor-operacao, #btn-gerar-duplicata, #msg-erro.
    2. Layout: Dark Theme (#1a1f2b).
    3. Critério: Exibir erro se campos obrigatórios estiverem vazios.
    Responda apenas o conteúdo da Story em Markdown.
    """

    res = ollama.chat(model='qwen2.5-coder', messages=[{'role': 'user', 'content': prompt}])
    conteudo = res['message']['content'].strip()

    issue_dict = {
        'project': 'KAN',
        'summary': '[ERP] Cadastro de Duplicatas - Squad Local',
        'description': conteudo,
        'issuetype': {'name': 'Story'},
    }
    
    nova_issue = jira.create_issue(fields=issue_dict)
    print(f"✅ Story {nova_issue.key} criada!")

if __name__ == "__main__":
    gerar_story_local()