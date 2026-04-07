const { defineConfig } = require("cypress");

module.exports = defineConfig({
  // Corrige o Warning de segurança sobre variáveis de ambiente
  allowCypressEnv: false, 
  
  e2e: {
    setupNodeEvents(on, config) {},
    video: false,
    reporter: 'mochawesome',
    reporterOptions: {
      reportDir: 'cypress/reports',
      overwrite: true,
      html: true,
      json: true,
      // ESTAS TRÊS LINHAS ABAIXO RESOLVEM O PROBLEMA DO "TUDO BRANCO":
      inline: true,
      inlineAssets: true,
      charts: true
    },
  },
});