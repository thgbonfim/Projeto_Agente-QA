import os
import subprocess
import time
import shutil
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(
    server=os.getenv("JIRA_SERVER") or os.getenv("JIRA_URL"), 
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN") or os.getenv("JIRA_API_TOKEN"))
)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def auditoria_pos_execucao():
    print("🕵️ [AUDITORIA] Inspecionando colunas de conclusão (Done)...")
    
    # O Auditor olha para o que o Testador já terminou
    issues = jira.search_issues('project="KAN" AND status="Done"')
    
    for issue in issues:
        # Verifica se já existe um Relatório HTML (para não entrar em loop)
        anexos = issue.fields.attachment
        ja_tem_html = any(a.filename.startswith("Auditoria_Premium") for a in anexos)

        if not ja_tem_html:
            print(f"🧐 {issue.key}: Transformando evidência bruta em HTML Premium...")
            
            # 1. PEGA O CONTEXTO (História + Plano)
            historia = issue.fields.description
            comentarios = [c.body for c in jira.comments(issue)]
            plano = next((c for c in comentarios if "PLANO DE TESTE" in c), "Teste padrão")

            # 2. GERA O CÓDIGO PARA O RELATÓRIO
            prompt = f"Gere Cypress para o plano: {plano}. Use o HTML do projeto. Responda apenas JS."
            codigo_js = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content.replace('```javascript', '').replace('```', '').strip()

            # 3. PREPARA O MOCHAWESOME
            os.makedirs('cypress/e2e', exist_ok=True)
            with open('cypress/e2e/auditoria_final.cy.js', 'w', encoding='utf-8') as f:
                f.write(codigo_js)

            if os.path.exists('cypress/reports'):
                shutil.rmtree('cypress/reports')

            # 4. GERA O REPORT BONITÃO
            print(f"🛰️ Compilando Relatório Mochawesome para {issue.key}...")
            comando = (
                "npx cypress run --spec cypress/e2e/auditoria_final.cy.js "
                "--reporter mochawesome "
                "--reporter-options reportDir=cypress/reports,overwrite=true,html=true,json=false"
            )
            subprocess.run(comando, shell=True, capture_output=True)

            # 5. SOBE O HTML PARA O JIRA
            report_gerado = "cypress/reports/auditoria_final.html"
            if os.path.exists(report_gerado):
                nome_formatado = f"Auditoria_Premium_{issue.key}.html"
                os.rename(report_gerado, nome_formatado)
                
                with open(nome_formatado, 'rb') as f:
                    jira.add_attachment(issue=issue.key, attachment=f)
                
                jira.add_comment(issue, "⭐ [AUDITORIA]: Evidência técnica convertida para formato HTML interativo.")
                print(f"✅ {issue.key} agora tem evidência de alta qualidade!")
                
                os.remove(nome_formatado)
            else:
                print(f"❌ Não foi possível gerar o HTML para {issue.key}")

if __name__ == "__main__":
    while True:
        try:
            auditoria_pos_execucao()
        except Exception as e:
            print(f"🔥 Erro na Auditoria: {e}")
        time.sleep(30)