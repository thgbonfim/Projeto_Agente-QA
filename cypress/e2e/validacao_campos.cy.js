describe('Cadastro de Duplicatas', () => {
  it('deve validar campos vazios', () => {
    cy.visit('http://localhost:8080');
    cy.get('#btn-gerar-duplicata').click();
    cy.get('#msg-erro').should('contain', 'obrigatórios');
  });

  it('deve preencher os inputs', () => {
    cy.visit('http://localhost:8080');
    cy.get('#input-razao-social').type('Empresa Teste');
    cy.get('#input-cnpj').type('12345678901234');
    cy.get('#input-valor-operacao').type('1000');
  });

  it('deve validar sucesso', () => {
    cy.visit('http://localhost:8080');
    cy.get('#input-razao-social').type('Empresa Teste');
    cy.get('#input-cnpj').type('12345678901234');
    cy.get('#input-valor-operacao').type('1000');
    cy.get('#btn-gerar-duplicata').click();
    cy.wait(2500);
    cy.get('#lista-duplicatas').should('contain', 'Empresa Teste');
  });

  it('deve evidenciar o sucesso', () => {
    cy.visit('http://localhost:8080');
    cy.get('#input-razao-social').type('Empresa Teste');
    cy.get('#input-cnpj').type('12345678901234');
    cy.get('#input-valor-operacao').type('1000');
    cy.get('#btn-gerar-duplicata').click();
    cy.wait(2500);
    cy.screenshot('evidencia_KAN-41');
  });
});