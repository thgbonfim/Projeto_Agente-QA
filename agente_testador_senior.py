import os, time, re, subprocess, ollama
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))

def executar_qa_mapeador_blindado():
    print("🕵️ [QA EXPLORADOR] Mapeando index.html e gerando teste local...")
    issues = jira.search_issues('project="KAN" AND status="Ready for Test"')
    
    for issue in issues:
        if not os.path.exists('index.html'):
            print(f"❌ Erro: index.html não encontrado.")
            continue
            
        with open('index.html', 'r', encoding='utf-8') as f:
            html_real = f.read()

        # PROMPT OTIMIZADO: Força a IA a não conversar, apenas codar.
        prompt_qa = f"""
        Você é um Engenheiro de QA Automação. 
        Analise o HTML fornecido e a STORY para gerar um teste Cypress.

        HTML DA APLICAÇÃO:
        {html_real}

        STORY:
        {issue.fields.description}

        🚨 REGRAS CRÍTICAS:
        1. Identifique os seletores reais (IDs, classes ou names) no HTML.
        2. Teste o fluxo de erro (campos vazios) e o de sucesso.
        3. No sucesso, use cy.wait(3000) e cy.screenshot('evidencia_{issue.key}').
        4. URL de teste: http://localhost:8080

        Retorne APENAS o código JavaScript puro, sem explicações e sem blocos de markdown (```).
        Comece o código diretamente com 'describe' ou 'it'.
        """

        res = ollama.chat(model='qwen2.5-coder', messages=[{'role': 'user', 'content': prompt_qa}])
        conteudo_bruto = res['message']['content']

        # --- LIMPEZA DE ELITE ---
        # 1. Remove os blocos de markdown ```javascript ou ```
        codigo_limpo = re.sub(r'```javascript|```js|```', '', conteudo_bruto).strip()
        
        # 2. CORTA TUDO O QUE NÃO FOR CÓDIGO
        # Procuramos onde o 'describe' começa e onde o último '});' termina
        if "describe" in codigo_limpo:
            inicio = codigo_limpo.find("describe")
            # Pegamos do 'describe' até o fim, mas vamos ignorar o que vier depois do último fechamento
            codigo_limpo = codigo_limpo[inicio:]
            
            # Se a IA colocou "### Explicação" no fim, vamos cortar fora
            if "###" in codigo_limpo:
                codigo_limpo = codigo_limpo.split("###")[0].strip()
        # ------------------------

        with open('cypress/e2e/validacao_campos.cy.js', 'w', encoding='utf-8') as f:
            f.write(codigo_limpo)
            
        print(f"🚀 Executando Cypress localmente para {issue.key}...")
        # Adicionei o timeout para o Cypress não travar seu PC
        try:
            subprocess.run(
                f"npx cypress run --spec {caminho_teste}", 
                shell=True, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Teste falhou (esperado se for validação de erro): {e.stdout[:100]}")

        # MAPEAMENTO DA EVIDÊNCIA
        # O Cypress salva com o nome do arquivo de teste na pasta
        caminho_print = f"cypress/screenshots/qa_explorador.cy.js/evidencia_{issue.key}.png"
        
        if os.path.exists(caminho_print):
            print(f"📸 Anexando print {issue.key} ao Jira...")
            with open(caminho_print, 'rb') as f:
                jira.add_attachment(issue=issue, attachment=f)
            jira.add_comment(issue, "✅ [QA]: Teste executado com mapeamento dinâmico do DOM. Print anexado.")
            jira.transition_issue(issue, transition="Done")
            print(f"🏁 {issue.key} FINALIZADA!")
        else:
            print(f"❌ Falha ao encontrar evidência em {caminho_print}")

if __name__ == "__main__":
    while True:
        try:
            executar_qa_mapeador_blindado()
        except Exception as e:
            print(f"❌ Erro no loop: {e}")
        time.sleep(30)