import os
import time
import re
import ollama  # <--- Trocamos Groq por Ollama
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

# Conexão com o Jira (Mantido igual)
jira = JIRA(
    server=os.getenv("JIRA_SERVER"), 
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))
)

def executar_desenvolvimento_elite_local():
    print("👀 [DEV LOCAL] Vigiando 'To Do' via Ollama (Qwen 2.5 Coder)...")
    issues = jira.search_issues('project="KAN" AND status="To Do"')
    
    for issue in issues:
        print(f"👨‍💻 Codando {issue.key} com foco em persistência de Layout...")
        requisitos = issue.fields.description if issue.fields.description else issue.fields.summary
        
        with open('index.html', 'r', encoding='utf-8') as f:
            codigo_atual = f.read()

        prompt_dev = f"""
        Você é um Desenvolvedor Front-end Senior. Atualize o 'index.html' seguindo esta Story:
        {requisitos}

        🚨 DIRETRIZES DE IMPLEMENTAÇÃO:
        1. MANUTENÇÃO: Não altere o CSS Dark (#1a1f2b) e o estilo dos cards atuais.
        2. VALIDAÇÃO: Se #input-cnpj ou #input-valor-operacao estiverem vazios, exiba "Campos obrigatórios" em #msg-erro.
        3. RENDERIZAÇÃO: Use Template Strings (crases ` ) no JS para inserir os dados.
        4. ESTILO DA LINHA: As novas <td> devem ter color: #e2e8f0 para serem visíveis no fundo escuro.
        
        CÓDIGO ATUAL:
        {codigo_atual}

        Responda APENAS o código completo sem markdown.
        """
        
        # --- CHAMADA AO OLLAMA LOCAL ---
        try:
            resposta = ollama.chat(
                model='qwen2.5-coder', # O modelo que você deu pull
                messages=[{'role': 'user', 'content': prompt_dev}]
            )
            
            conteudo_ia = resposta['message']['content'].strip()
            
            # Limpeza de segurança (Regex)
            novo_codigo = re.sub(r'```[a-z]*', '', conteudo_ia).replace('```', '').strip()

            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(novo_codigo)
            
            jira.add_comment(issue, "🚀 [DEV LOCAL]: Implementado via Ollama (Qwen 2.5 Coder) com layout preservado.")
            jira.transition_issue(issue, transition="Ready for Test")
            print(f"✅ {issue.key} enviada para o QA!")
            
        except Exception as e:
            print(f"❌ Erro na chamada do Ollama: {e}")

if __name__ == "__main__":
    while True:
        try: 
            executar_desenvolvimento_elite_local()
        except Exception as e: 
            print(f"❌ Erro no DEV: {e}")
        time.sleep(30)