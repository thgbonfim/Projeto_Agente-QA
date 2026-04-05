import os
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def gerar_historia_erp_duplicatas():
    print("🧠 P.O. Analisando Regras do Módulo de Duplicatas...")
    
    # Prompt avançado focado em ERP e Inventário
    prompt = """
    Você é um Product Owner de ERP Bancário. Sua missão é criar uma Story técnica para o 'Módulo de Duplicatas'.
    
    CONTEXTO DO PRODUTO (HTML):
    - Nome: ERP INVENTÁRIO - MÓDULO DUPLICATAS.
    - Campos: Razão Social, CNPJ do Sacado, Valor Nominal.
    - Comportamento: O sistema simula um delay de 2.5s de integração e insere na 'Grade de Inventário'.
    
    ESTRUTURA DA STORY:
    1. Título focado em 'Registro de Título no Inventário'.
    2. User Story: (Como Analista Financeiro... Quero registrar duplicatas PJ... Para controle de inventário).
    3. Critérios de Aceite Rigorosos:
       - Validação de campos obrigatórios (Razão, CNPJ, Valor).
       - Verificação de que o título aparece na tabela após o 'Loading'.
       - O status do novo título deve ser 'PROCESSADO'.
    4. Cenário Gherkin para o QA:
       Dado que estou no Módulo de Duplicatas, Quando preencho os dados PJ corretamente e clico em Confirmar, Então o título deve constar na Grade de Inventário.

    Responda apenas o conteúdo da Task (Markdown).
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6 # Menos criatividade, mais precisão técnica
    )
    
    return completion.choices[0].message.content

def enviar_ao_jira(conteudo):
    print("📝 Enviando Requisito de Negócio ao Jira...")
    
    # Pega o título da primeira linha ou gera um padrão
    titulo_limpo = conteudo.split('\n')[0].replace("#", "").replace("Título:", "").strip()
    
    issue_dict = {
        'project': 'KAN',
        'summary': f'[ERP-DUPLICATAS] {titulo_limpo}',
        'description': conteudo,
        'issuetype': {'name': 'Story'},
    }
    
    new_issue = jira.create_issue(fields=issue_dict)
    print(f"✅ Story de Inventário Criada: {new_issue.key}")
    return new_issue.key

if __name__ == "__main__":
    conteudo_story = gerar_historia_erp_duplicatas()
    enviar_ao_jira(conteudo_story)