import os
import subprocess
import time
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def executar_testes_com_evidencia():
    print("👀 [TESTADOR] Vigiando Ready for Test para validar e coletar evidências...")
    issues = jira.search_issues('project="KAN" AND status="Ready for Test"')
    
    for issue in issues:
        comentarios = jira.comments(issue)
        plano_comentado = next((c.body for c in comentarios if "PLANO DE TESTE" in c.body), None)

        if plano_comentado:
            print(f"🚀 {issue.key}: Plano encontrado! Gerando teste e evidências...")
            
            with open('index.html', 'r', encoding='utf-8') as f:
                html = f.read()

            # Gerando código com comando de Screenshot do Cypress
            prompt_code = f"""
            Crie o Cypress para: {plano_comentado}. HTML: {html}. 
            REGRAS:
            - Use cy.visit('http://localhost:8080').
            - No final do teste, use cy.screenshot('evidencia_{issue.key}').
            - Responda apenas o código JS.
            """
            codigo = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt_code}]
            ).choices[0].message.content.replace('```javascript', '').replace('```', '').strip()

            os.makedirs('cypress/e2e', exist_ok=True)
            with open('cypress/e2e/duplicatas.cy.js', 'w', encoding='utf-8') as f:
                f.write(codigo)

            # Executa o Cypress
            result = subprocess.run(
                "npx cypress run --spec cypress/e2e/duplicatas.cy.js",
                capture_output=True, text=True, shell=True, encoding='utf-8', errors='replace'
            )
            
            # Caminho da evidência (O Cypress salva por padrão em screenshots/nome_do_arquivo/...)
            # Vamos simplificar buscando o arquivo gerado
            caminho_print = f"cypress/screenshots/duplicatas.cy.js/evidencia_{issue.key}.png"

            if "All specs passed" in (result.stdout or ""):
                # ANEXAR EVIDÊNCIA NO JIRA
                if os.path.exists(caminho_print):
                    jira.add_attachment(issue=issue, attachment=caminho_print)
                    print(f"📸 Evidência anexada à {issue.key}!")
                
                jira.transition_issue(issue, transition="Done")
                jira.add_comment(issue, "✅ Teste PASSOU. Evidência anexada aos arquivos da Task.")
                print(f"🏁 {issue.key} FINALIZADA COM PROVAS!")
            else:
                # Se falhou, anexa o print do erro também!
                if os.path.exists(caminho_print):
                    jira.add_attachment(issue=issue, attachment=caminho_print)
                
                jira.add_comment(issue, f"❌ Teste FALHOU. Veja o print anexado e o log abaixo:\n\n{result.stdout[:300]}")
                print(f"⚠️ {issue.key} FALHOU, mas a evidência do erro está no Jira!")
        else:
            print(f"⏳ {issue.key} aguardando o Analista...")

if __name__ == "__main__":
    while True:
        try:
            executar_testes_com_evidencia()
        except Exception as e:
            print(f"❌ Erro Testador: {e}")
        time.sleep(30)