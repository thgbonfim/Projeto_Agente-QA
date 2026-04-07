import os
import time
import re
import ollama  # Trocamos Groq por Ollama local
from jira import JIRA
from dotenv import load_dotenv

# Carrega as configurações do seu .env
load_dotenv()

# Conexão com o Jira (Thiago Bonfim - Accenture Brasil)
jira = JIRA(
    server=os.getenv("JIRA_SERVER"), 
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))
)

def planejar_testes_local():
    print("👀 [ANALISTA LOCAL] Vigiando 'Ready for Test' para planejar cenários...")
    # O Analista vigia a coluna onde o DEV acabou de entregar o código
    issues = jira.search_issues('project="KAN" AND status="Ready for Test"')
    
    for issue in issues:
        # Verifica se o Analista já deixou o plano para não repetir o trabalho
        comentarios = jira.comments(issue)
        ja_planejado = any("PLANO DE TESTE" in c.body for c in comentarios)

        if not ja_planejado:
            print(f"🧠 Planejando cenários Gherkin para {issue.key}...")
            
            # Recupera a Story escrita pelo seu Agente P.O.
            requisitos = issue.fields.description if issue.fields.description else issue.fields.summary
            
            # Prompt focado em gerar BDD/Gherkin puro para o Testador codar depois
            prompt = f"""
            Você é um Analista de QA Sênior especialista em BDD.
            Analise esta Story técnica: {requisitos}

            Sua missão é criar cenários GHERKIN detalhados.
            
            REGRAS:
            1. Use os IDs técnicos mencionados na Story (ex: #input-razao-social).
            2. Foque em: Caminho Feliz e Validação de Campos Vazios.
            3. Responda apenas o Markdown do Gherkin, sem introduções.
            """
            
            try:
                # Chamada ao Ollama (Llama 3 local)
                response = ollama.chat(
                    model='llama3',
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Extração do conteúdo limpando possíveis marcações de chat
                plano_bruto = response['message']['content'].strip()
                plano_limpo = re.sub(r'```[a-z]*', '', plano_bruto).replace('```', '').strip()

                # Adiciona o comentário com o cabeçalho que o Testador Senior reconhece
                jira.add_comment(issue, f"📝 **PLANO DE TESTE AUTOMÁTICO:**\n\n{plano_limpo}")
                print(f"✅ {issue.key} planejada! Aguardando o Testador agir localmente.")
                
            except Exception as e:
                print(f"❌ Erro ao processar IA local: {e}")

if __name__ == "__main__":
    while True:
        try:
            planejar_testes_local()
        except Exception as e:
            print(f"❌ Erro no Agente Analista: {e}")
        # Intervalo para não sobrecarregar o processador com o Ollama
        time.sleep(30)