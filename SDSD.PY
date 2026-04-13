so pega esse cosigo e arruma co a evidencia em html import os

import time

import re

import ollama  # Trocamos Groq por Ollama

from jira import JIRA

from dotenv import load_dotenv



# Carrega variáveis de ambiente (.env)

load_dotenv()



# Conexão com o Jira

jira = JIRA(

    server=os.getenv("JIRA_SERVER"), 

    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))

)



def executar_desenvolvimento():

    print("👀 [DEV FULLSTACK] Vigiando coluna 'To Do' via Ollama Local...")

    # Busca tarefas que o P.O. criou

    issues = jira.search_issues('project="KAN" AND status="To Do"')

    

    for issue in issues:

        print(f"👨‍💻 Desenvolvendo solução para {issue.key}...")

        requisitos = issue.fields.description if issue.fields.description else issue.fields.summary

        

        # O DEV lê o index.html atual para contexto

        if not os.path.exists('index.html'):

            # Cria um arquivo base caso não exista

            with open('index.html', 'w', encoding='utf-8') as f:

                f.write("<!DOCTYPE html><html><body></body></html>")



        with open('index.html', 'r', encoding='utf-8') as f:

            codigo_atual = f.read()



        # Prompt ajustado para o Llama 3 local

        prompt_dev = f"""

        Você é um Desenvolvedor Front-end Sênior especialista em sistemas bancários.

        Sua missão é IMPLEMENTAR a funcionalidade descrita no requisito abaixo no HTML existente.



        REQUISITO: {requisitos}

        CÓDIGO ATUAL: {codigo_atual}



        REGRAS:

        1. Retorne APENAS o código HTML/CSS/JS completo.

        2. NÃO use markdown (```html).

        3. NÃO explique nada, apenas entregue o código funcional.

        4. Garanta que os IDs solicitados pelo P.O. estejam corretos.

        """

        

        print(f"⏳ Ollama (Llama 3) processando {issue.key}...")

        

        # Chamada ao Ollama Local

        resposta = ollama.chat(

            model='llama3', 

            messages=[{"role": "user", "content": prompt_dev}]

        )

        

        conteudo_ia = resposta['message']['content'].strip()



        # --- FILTRO DE LIMPEZA ---

        # Extrai apenas o bloco HTML para evitar que textos de "conversa" da IA entrem no arquivo

        match = re.search(r'(<!DOCTYPE.*?</html>|<html.*?</html>)', conteudo_ia, re.DOTALL | re.IGNORECASE)

        

        if match:

            codigo_final = match.group(1).strip()

        else:

            # Caso a IA não mande as tags completas, removemos apenas os blocos de markdown

            codigo_final = re.sub(r'```[a-z]*', '', conteudo_ia).replace('```', '').strip()



        # O DEV salva o trabalho dele no arquivo real

        with open('index.html', 'w', encoding='utf-8') as f:

            f.write(codigo_final)

        

        # Move para Ready for Test para o QA assumir

        jira.add_comment(issue, "🚀 [DEV]: Código implementado localmente via Ollama e arquivo index.html atualizado!")

        jira.transition_issue(issue, transition="Ready for Test")

        print(f"✅ {issue.key} Codada e enviada para Teste!")



if __name__ == "__main__":

    while True:

        try:

            executar_desenvolvimento()

        except Exception as e:

            print(f"❌ Erro no DEV: {e}")

        time.sleep(30)