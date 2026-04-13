describe('Cadastro de Duplicatas', () => {
    it('Deve cadastrar uma duplicata com sucesso', () => {
        cy.visit('http://localhost:8080');

        cy.get('#input-razao-social').type('Empresa Teste');
        cy.get('#input-cnpj').type('12345678901234');
        cy.get('#input-valor-operacao').type('100.00');

        cy.get('#btn-gerar-duplicata').click();

        cy.contains(' Registro efetuado com sucesso!').should('be.visible');
        cy.wait(3000);
        cy.screenshot('evidencia_KAN-57');
    });

    it('Não deve cadastrar duplicata se campos obrigatórios estiverem vazios', () => {
        cy.visit('http://localhost:8080');

        cy.get('#input-cnpj').type('12345678901234');
        cy.get('#input-valor-operacao').type('100.00');

        cy.get('#btn-gerar-duplicata').click();

        cy.contains(' Erro: Preencha todos os campos obrigatórios.').should('be.visible');
    });
});