import os
import time
import re
import subprocess
import ollama
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(
    server=os.getenv("JIRA_SERVER"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))
)

PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")
MAX_TENTATIVAS = 3


def detectar_mensagem_validacao(html: str) -> dict:
    html_lower = html.lower()

    if "preencha todos os campos obrigatórios" in html_lower:
        return {
            "tipo": "generica",
            "mensagem": "Preencha todos os campos obrigatórios"
        }

    mensagens_especificas = []

    if "razão social" in html_lower and "obrigat" in html_lower:
        mensagens_especificas.append("Razão Social")
    if "cnpj" in html_lower and "obrigat" in html_lower:
        mensagens_especificas.append("CNPJ")
    if "valor" in html_lower and "obrigat" in html_lower:
        mensagens_especificas.append("Valor")

    if mensagens_especificas:
        return {
            "tipo": "especifica",
            "campos": mensagens_especificas
        }

    return {
        "tipo": "generica",
        "mensagem": "Erro"
    }


def limpar_codigo_js(texto: str) -> str:
    codigo = re.sub(r"```(?:javascript|js)?", "", texto, flags=re.IGNORECASE)
    codigo = re.sub(r"```", "", codigo).strip()

    if "describe" in codigo:
        codigo = codigo[codigo.find("describe"):]

    return codigo.strip()


def gerar_teste_baseado_no_html(html: str, issue_key: str) -> str:
    regra_validacao = detectar_mensagem_validacao(html)

    if regra_validacao["tipo"] == "generica":
        bloco_validacao = f"""
  it('deve exibir mensagem de erro para campos obrigatórios em branco', () => {{
    cy.visit('http://localhost:8080')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#msg-erro')
      .should('be.visible')
      .and('contain', '{regra_validacao["mensagem"]}')
  }})
"""
    else:
        asserts = "\n".join([
            f"    cy.get('#msg-erro').should('contain', '{campo}')"
            for campo in regra_validacao["campos"]
        ])

        bloco_validacao = f"""
  it('deve exibir mensagens de erro para campos obrigatórios em branco', () => {{
    cy.visit('http://localhost:8080')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#msg-erro').should('be.visible')
{asserts}
  }})
"""

    codigo = f"""describe('Cadastro de Duplicatas - {issue_key}', () => {{

  it('deve cadastrar uma duplicata com sucesso', () => {{
    cy.visit('http://localhost:8080')

    cy.get('#input-razao-social').type('Empresa Teste LTDA')
    cy.get('#input-cnpj').type('12345678901234')
    cy.get('#input-valor-operacao').type('100.00')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#msg-sucesso', {{ timeout: 10000 }})
      .should('be.visible')
      .and('contain', 'Registro efetuado com sucesso')

    cy.get('#lista-duplicatas tr').should('have.length.at.least', 1)
    cy.get('#contador-titulos').should('contain', '1 títulos encontrados')

    cy.screenshot('evidencia_{issue_key}')
  }})

{bloco_validacao}

  it('deve apagar uma duplicata do inventário', () => {{
    cy.visit('http://localhost:8080')

    cy.get('#input-razao-social').type('Empresa Delete LTDA')
    cy.get('#input-cnpj').type('98765432100000')
    cy.get('#input-valor-operacao').type('250.00')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#lista-duplicatas tr').should('have.length.at.least', 1)

    cy.get('#lista-duplicatas tr').first().find('button').click()

    cy.get('#feedback-sistema', {{ timeout: 10000 }})
      .should('be.visible')
      .and('contain', 'Título removido')

    cy.get('#contador-titulos').should('contain', '0 títulos encontrados')
  }})

}})
"""
    return codigo


def gerar_teste_com_ia(html: str, story: str, issue_key: str) -> str:
    prompt = f"""
Você é um QA especialista em Cypress.

HTML:
{html}

STORY:
{story}

REGRAS:
- Use apenas IDs reais do HTML
- Gere apenas 3 cenários:
  1. cadastro com sucesso
  2. apagar duplicata
  3. validar mensagem de campos obrigatórios
- Se o sistema exibir mensagem genérica, valide a mensagem genérica
- Não invente mensagens específicas se não existirem no HTML
- URL: http://localhost:8080
- use cy.screenshot('evidencia_{issue_key}') no cenário de sucesso

Retorne apenas código Cypress válido.
"""
    res = ollama.chat(
        model="qwen2.5-coder",
        messages=[{"role": "user", "content": prompt}]
    )
    return limpar_codigo_js(res["message"]["content"])


def executar_cypress(caminho_teste: str):
    return subprocess.run(
        ["npx.cmd", "cypress", "run", "--spec", caminho_teste],
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )


def corrigir_teste_local(codigo: str, erro: str, html: str) -> str:
    erro_lower = erro.lower()

    if "o campo razão social é obrigatório".lower() in erro_lower:
        regra = detectar_mensagem_validacao(html)
        if regra["tipo"] == "generica":
            codigo = re.sub(
                r"cy\.get\('#msg-erro'\)\.should\('contain',\s*'O campo Razão Social é obrigatório'\)\s*",
                "",
                codigo
            )
            codigo = re.sub(
                r"cy\.get\('#msg-erro'\)\.should\('contain',\s*'O campo CNPJ.*?'\)\s*",
                "",
                codigo
            )
            codigo = re.sub(
                r"cy\.get\('#msg-erro'\)\.should\('contain',\s*'O campo Valor.*?'\)\s*",
                "",
                codigo
            )

            codigo = codigo.replace(
                "cy.get('#msg-erro').should('be.visible')",
                "cy.get('#msg-erro').should('be.visible').and('contain', 'Preencha todos os campos obrigatórios')"
            )

    return codigo


def mover_para_final(issue):
    transicoes = jira.transitions(issue)

    nomes_preferidos = [
        "Done",
        "Concluir",
        "Finalizar",
        "Encerrar",
        "Close Issue",
        "Resolve Issue"
    ]

    for nome in nomes_preferidos:
        for t in transicoes:
            if t["name"].strip().lower() == nome.strip().lower():
                jira.transition_issue(issue, t["id"])
                print(f"✅ Issue {issue.key} movida com a transição: {t['name']}")
                return True

    print(f"⚠️ Nenhuma transição final encontrada para {issue.key}")
    print("🔄 Transições disponíveis:")
    for t in transicoes:
        print(f"- id={t['id']} | name={t['name']}")
    return False


def executar_qa_inteligente():
    print("🧠 [QA HTML-AWARE] Rodando...")

    issues = jira.search_issues(
        f'project="{PROJECT_KEY}" AND status="Ready for Test"',
        maxResults=10
    )

    for issue in issues:
        print(f"\n🎫 Processando {issue.key}")

        if not os.path.exists("index.html"):
            print("❌ index.html não encontrado")
            continue

        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()

        caminho_teste = f"cypress/e2e/{issue.key}.cy.js"
        caminho_print = f"cypress/screenshots/{issue.key}.cy.js/evidencia_{issue.key}.png"

        codigo = gerar_teste_baseado_no_html(html, issue.key)

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            print(f"🔁 Tentativa {tentativa}")

            os.makedirs("cypress/e2e", exist_ok=True)

            with open(caminho_teste, "w", encoding="utf-8") as f:
                f.write(codigo)

            result = executar_cypress(caminho_teste)

            if result.returncode == 0:
                print("✅ Teste passou")

                if os.path.exists(caminho_print):
                    jira.add_attachment(issue=issue, attachment=caminho_print)

                jira.add_comment(issue, "✅ Teste validado com QA que entende o HTML.")
                mover_para_final(issue)
                break

            erro = (result.stderr or "") + (result.stdout or "")
            print(f"❌ Erro detectado:\n{erro[:800]}")

            novo_codigo = corrigir_teste_local(codigo, erro, html)

            if novo_codigo != codigo:
                print("🛠️ Correção local aplicada com base no HTML")
                codigo = novo_codigo
                continue

            print("🤖 Fallback para IA")
            codigo = gerar_teste_com_ia(html, issue.fields.description, issue.key)

        else:
            jira.add_comment(issue, "❌ Teste falhou após tentativas automáticas.")
            print("❌ Falhou após tentativas")


if __name__ == "__main__":
    while True:
        try:
            executar_qa_inteligente()
        except Exception as e:
            print(f"❌ Erro geral: {e}")

        time.sleep(30)