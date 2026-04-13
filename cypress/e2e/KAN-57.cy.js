describe('Cadastro de Duplicatas - KAN-57', () => {

  it('deve cadastrar uma duplicata com sucesso', () => {
    cy.visit('http://localhost:8080')

    cy.get('#input-razao-social').type('Empresa Teste LTDA')
    cy.get('#input-cnpj').type('12345678901234')
    cy.get('#input-valor-operacao').type('100.00')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#msg-sucesso', { timeout: 10000 })
      .should('be.visible')
      .and('contain', 'Registro efetuado com sucesso')

    cy.get('#lista-duplicatas tr').should('have.length.at.least', 1)
    cy.get('#contador-titulos').should('contain', '1 títulos encontrados')

    cy.screenshot('evidencia_KAN-57')
  })


  it('deve exibir mensagem de erro para campos obrigatórios em branco', () => {
    cy.visit('http://localhost:8080')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#msg-erro')
      .should('be.visible')
      .and('contain', 'Preencha todos os campos obrigatórios')
  })


  it('deve apagar uma duplicata do inventário', () => {
    cy.visit('http://localhost:8080')

    cy.get('#input-razao-social').type('Empresa Delete LTDA')
    cy.get('#input-cnpj').type('98765432100000')
    cy.get('#input-valor-operacao').type('250.00')

    cy.get('#btn-gerar-duplicata').click()

    cy.get('#lista-duplicatas tr').should('have.length.at.least', 1)

    cy.get('#lista-duplicatas tr').first().find('button').click()

    cy.get('#feedback-sistema', { timeout: 10000 })
      .should('be.visible')
      .and('contain', 'Título removido')

    cy.get('#contador-titulos').should('contain', '0 títulos encontrados')
  })

})
