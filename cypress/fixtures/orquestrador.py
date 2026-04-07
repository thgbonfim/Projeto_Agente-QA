import os, time, re, ollama
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
jira = JIRA(server=os.getenv("JIRA_SERVER"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))

def executar_dev_senior():
    print("👀 [DEV SENIOR] Vigiando To Do para entregar interface profissional...")
    issues = jira.search_issues('project="KAN" AND status="To Do"')
    
    for issue in issues:
        print(f"🎨 Estilizando e codando {issue.key}...")
        
        prompt = f"""
        Você é um Desenvolvedor Front-end Senior com foco em UI/UX Bancário.
        Sua missão é implementar a Story: {issue.fields.description}.

        DIRETRIZES DE DESIGN OBRIGATÓRIAS:
        1. CSS INTERNO: Use uma paleta de cores profissional (Azul marinho, Cinza claro, Branco).
        2. TABELA: Use a tag <table> real com <thead>, <tbody>, bordas arredondadas e efeito zebra nas linhas.
        3. INPUTS: Estilize com padding, border-radius e foco azul. Adicione labels claros.
        4. FEEDBACK VISUAL: O botão deve mudar de cor no hover e ficar cinza quando 'disabled'.
        5. IDs CRÍTICOS: Mantenha rigorosamente os IDs solicitados para o QA.

        COMPORTAMENTO JS:
        - Ao clicar em #btn-gerar-duplicata:
            - Validar se campos estão vazios -> mostrar erro em #validacao-erro (cor vermelha).
            - Se OK -> Limpar erro, desabilitar botão, exibir "Processando..." em #feedback-sistema.
            - Aguardar 2.5s -> Inserir na <tbody> de #lista-duplicatas, reabilitar botão e limpar inputs.

        Retorne APENAS o código HTML/CSS/JS COMPLETO. Sem markdown e sem explicações.
        """
        
        res = ollama.chat(model='llama3', messages=[{"role": "user", "content": prompt}])
        conteudo_bruto = res['message']['content'].strip()

        # --- LÓGICA DE EXTRAÇÃO DE ELITE ---
        # Isola o HTML real ignorando qualquer "conversa" da IA antes ou depois
        match = re.search(r'(<!DOCTYPE.*?</html>|<html.*?</html>)', conteudo_bruto, re.DOTALL | re.IGNORECASE)

        if match:
            codigo_limpo = match.group(1).strip() # Extrai apenas o bloco de código
        else:
            # Fallback: remove apenas os blocos de markdown se a estrutura completa falhar
            codigo_limpo = re.sub(r'```[a-z]*', '', conteudo_bruto).replace('```', '').strip()

        # Salva o arquivo sem ruídos de texto
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(codigo_limpo)
        
        jira.transition_issue(issue, transition="Ready for Test")
        jira.add_comment(issue, "🚀 [DEV]: Sistema implementado com UI/UX profissional. Arquivo limpo gerado.")
        print(f"✅ {issue.key} finalizada com sucesso e limpa!")

if __name__ == "__main__":
    while True:
        try:
            executar_dev_senior()
        except Exception as e:
            print(f"❌ Erro no DEV: {e}")
        time.sleep(20)