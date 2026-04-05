describe('Teste de Duplicatas', () => {
  beforeEach(() => {
    cy.visit('http://localhost:8080')
  })

  it('Deve registrar uma nova operação', () => {
    cy.get('#razao-social').type('Accenture Brasil')
    cy.get('#documento-cnpj').type('00.000.000/0000-00')
    cy.get('#valor-operacao').type('1000')
    cy.get('#btn-gerar-duplicata').click()

    cy.get('#feedback-sistema', { timeout: 3000 }).should('be.visible')
    cy.get('#feedback-sistema', { timeout: 3000 }).should('contain', 'Operação registrada no inventário com sucesso!')
  })

  it('Não deve registrar uma nova operação com campos vazios', () => {
    cy.get('#btn-gerar-duplicata').click()

    cy.get('#feedback-sistema', { timeout: 3000 }).should('be.visible')
    cy.get('#feedback-sistema', { timeout: 3000 }).should('contain', 'ERRO: Preencha todos os campos da duplicata!')
  })

  it('Deve exibir a lista de duplicatas', () => {
    cy.get('#lista-duplicatas tr').should('have.length', 1)
  })

  it('Deve adicionar uma nova duplicata à lista', () => {
    cy.get('#razao-social').type('Accenture Brasil')
    cy.get('#documento-cnpj').type('00.000.000/0000-00')
    cy.get('#valor-operacao').type('1000')
    cy.get('#btn-gerar-duplicata').click()

    cy.get('#lista-duplicatas tr', { timeout: 3000 }).should('have.length', 2)
  })
})