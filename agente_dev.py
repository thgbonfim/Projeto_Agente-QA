import os
import time
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def executar_desenvolvimento():
    print("👀 [DEV] Vigiando coluna 'To Do' para codar...")
    # Busca tarefas que o P.O. acabou de criar
    issues = jira.search_issues('project="KAN" AND status="To Do"')
    
    for issue in issues:
        print(f"👨‍💻 Desenvolvendo solução para {issue.key}...")
        requisitos = issue.fields.description
        
        # O DEV lê o index.html atual para saber onde inserir a nova funcionalidade
        with open('index.html', 'r', encoding='utf-8') as f:
            codigo_atual = f.read()

        prompt_dev = f"""
        Você é um Desenvolvedor Front-end Sênior. 
        REQUISITO: {requisitos}
        CÓDIGO ATUAL: {codigo_atual}
        
        Sua tarefa: Atualize o código do 'index.html' para incluir o que foi pedido.
        Mantenha o design limpo e use os IDs corretos para o QA não quebrar.
        Responda APENAS o código HTML/CSS/JS completo, sem explicações.
        """
        
        novo_codigo = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_dev}]
        ).choices[0].message.content.replace('```html', '').replace('```', '').strip()

        # O DEV salva o trabalho dele no arquivo real
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(novo_codigo)
        
        # Move para Ready for Test para o QA Analista assumir
        jira.add_comment(issue, "🚀 [DEV]: Código implementado e arquivo index.html atualizado!")
        jira.transition_issue(issue, transition="Ready for Test")
        print(f"✅ {issue.key} Codada e enviada para Teste!")

if __name__ == "__main__":
    while True:
        try:
            executar_desenvolvimento()
        except Exception as e:
            print(f"❌ Erro no DEV: {e}")
        time.sleep(30)