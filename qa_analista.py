import os
import time
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def planejar_testes():
    print("👀 [ANALISTA] Vigiando Ready for Test para planejar...")
    # O Analista agora vigia onde o DEV entregou
    issues = jira.search_issues('project="KAN" AND status="Ready for Test"')
    
    for issue in issues:
        # Verifica se o Analista já comentou nesta issue (para não comentar mil vezes)
        comentarios = jira.comments(issue)
        ja_planejado = any("PLANO DE TESTE" in c.body for c in comentarios)

        if not ja_planejado:
            print(f"🧠 Planejando cenários para {issue.key}...")
            requisitos = issue.fields.description if issue.fields.description else issue.fields.summary
            
            prompt = f"Analise esta Story: {requisitos}. Crie os cenários Gherkin. Responda em Markdown."
            
            plano = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

            # Adiciona o plano como comentário, mas MANTÉM na mesma coluna
            jira.add_comment(issue, f"📝 **PLANO DE TESTE AUTOMÁTICO:**\n\n{plano}")
            print(f"✅ {issue.key} planejada! Aguardando o Testador agir.")

if __name__ == "__main__":
    while True:
        try:
            planejar_testes()
        except Exception as e:
            print(f"❌ Erro Analista: {e}")
        time.sleep(30)