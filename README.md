# 🚜 Squad Digital Autônoma - AI Driven (Llama 3.3 + Jira)

Este projeto demonstra uma pipeline de software 100% automatizada e orquestrada por Agentes de IA independentes.

## 🤖 Agentes da Squad
1. **Agente DEV**: Monitora o 'To Do', implementa código no `index.html` e move para teste.
2. **QA Analista**: Monitora o 'Ready for Test', planeja cenários Gherkin e comenta na Task.
3. **QA Testador**: Lê o plano do analista, gera código Cypress em tempo real, executa e anexa evidências no Jira.

## 🛠️ Stack Técnica
- **Cérebro**: Groq Cloud (Llama 3.3 70b)
- **Gestão**: Jira Software API
- **Automação**: Cypress.io
- **Linguagem**: Python 3.13 (Orquestração de Agentes)
