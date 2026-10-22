"""Ferramentas financeiras: chamadas HTTP para o backend Node.js.

IDs e valores decimais usam strings; datas usam YYYY-MM-DD.
Retornos incluem ok, data ou error e metadados de paginação nas listas.
"""

from typing import Any

from langchain_core.tools import tool

from app.core.backend import path_id, payload, request


@tool
def consultar_resumo_financeiro(year: int, month: int) -> dict[str, Any]:
    """
    Recebe ano e mês. Retorna receitas, despesas, pendências, gastos por categoria,
    saldos atuais das contas e próximos vencimentos.
    API: GET /dashboard?year=...&month=...
    Uso: "Como estão minhas finanças este mês?"
    Atenção: balance é saldo atual, não saldo histórico do mês consultado;
    upcoming_bills traz até dez contas não pagas, sem limitar ao mês solicitado.
    """
    return request("GET", '/dashboard', params=payload(locals()))


@tool
def listar_contas() -> dict[str, Any]:
    """
    Retorna IDs, nomes, tipos, situação e saldo calculado das contas.
    API: GET /accounts
    Uso: descobrir qual conta o usuário chamou de "Nubank" ou "carteira".
    Se houver nomes iguais ou ambíguos, apresentar opções antes de escolher.
    """
    return request("GET", '/accounts')


@tool
def consultar_conta(account_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna os dados e saldo atual de uma conta específica.
    API: GET /accounts/:id
    Uso: "Quanto tenho na minha conta?"
    Utilizar balance retornado pela API; initial_balance é apenas o saldo inicial.
    """
    return request("GET", f"/accounts/{path_id(account_id)}")


@tool
def listar_categorias() -> dict[str, Any]:
    """
    Retorna IDs, nomes e tipos para identificar categorias de receita/despesa.
    API: GET /categories
    A ferramenta poderá selecionar o tipo na lista retornada; a rota atual
    não implementa filtro por tipo. Não inventar categorias ou IDs.
    """
    return request("GET", '/categories')


@tool
def buscar_lancamentos(
    start_date: str | None = None,
    end_date: str | None = None,
    account_id: str | None = None,
    credit_card_id: str | None = None,
    category_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Recebe período, conta, cartão, categoria, tipo, situação e paginação opcionais.
    API: GET /transactions
    Filtros existentes: start_date, end_date, account_id, credit_card_id,
    category_id, type, status, limit, offset.
    Retorna registros com valores, datas, nomes relacionados e is_editable.
    Uso: "Mostre meus gastos com alimentação em setembro."
    A API ainda não busca por texto da descrição. Não enviar filtro inexistente.
    Uma página de registros não representa necessariamente todo o período.
    """
    return request("GET", '/transactions', params=payload(locals()))


@tool
def consultar_lancamento(transaction_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna os detalhes de um lançamento.
    API: GET /transactions/:id
    Uso: conferir valor, conta e data antes de uma correção.
    is_editable é fornecido na listagem; a consulta individual não o calcula.
    """
    return request("GET", f"/transactions/{path_id(transaction_id)}")


@tool
def listar_contas_a_pagar(
    status: str | None = None,
    account_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Recebe situação, conta, período de vencimento e paginação opcionais.
    API: GET /bills?status=...&account_id=...&start_date=...&end_date=...
    Retorna obrigações pendentes, vencidas ou pagas, com recorrência.
    Uso: "Quais contas vencem nesta semana?"
    Não confundir uma obrigação em bills com uma despesa já realizada.
    """
    return request("GET", '/bills', params=payload(locals()))


@tool
def consultar_conta_a_pagar(bill_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna vencimento, valor, categoria, conta e situação.
    API: GET /bills/:id
    Uso: identificar exatamente qual boleto/conta o usuário quer registrar como pago.
    """
    return request("GET", f"/bills/{path_id(bill_id)}")


@tool
def listar_cartoes() -> dict[str, Any]:
    """
    Retorna cartões, IDs, conta de pagamento, limite cadastrado e dias da fatura.
    API: GET /credit-cards
    Uso: identificar o cartão usado numa compra.
    credit_limit é o limite cadastrado, não o limite disponível calculado.
    """
    return request("GET", '/credit-cards')


@tool
def consultar_cartao(credit_card_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna os dados de um cartão.
    API: GET /credit-cards/:id
    Uso: consultar fechamento, vencimento ou conta usada no pagamento.
    """
    return request("GET", f"/credit-cards/{path_id(credit_card_id)}")


@tool
def listar_faturas(credit_card_id: str | None = None, status: str | None = None) -> dict[str, Any]:
    """
    Recebe cartão e situação opcionais; retorna faturas com total e pendências.
    APIs: GET /invoices?credit_card_id=...&status=...
    ou GET /credit-cards/:id/invoices
    Uso: "Quanto está a fatura do meu cartão?"
    Se houver várias faturas, identificar o mês antes de selecionar uma.
    """
    return request("GET", '/invoices', params=payload(locals()))


@tool
def consultar_fatura(invoice_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna datas, situação, total, valor pendente e compras.
    API: GET /invoices/:id
    Uso: explicar quais compras compõem determinada fatura.
    """
    return request("GET", f"/invoices/{path_id(invoice_id)}")


@tool
def listar_orcamentos(year: int | None = None, month: int | None = None) -> dict[str, Any]:
    """
    Recebe ano e mês opcionais; retorna limites, gasto realizado e valor restante
    por categoria. API: GET /budgets?year=...&month=...
    Uso: "Quanto ainda posso gastar com alimentação dentro do meu orçamento?"
    """
    return request("GET", '/budgets', params=payload(locals()))


@tool
def consultar_orcamento(budget_id: str) -> dict[str, Any]:
    """
    Recebe ID e retorna os dados e acompanhamento de um orçamento.
    API: GET /budgets/:id
    """
    return request("GET", f"/budgets/{path_id(budget_id)}")


@tool
def listar_transferencias(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """
    Recebe limit/offset e retorna transferências agrupadas entre contas.
    API: GET /transfers
    Não contabilizar como receita ou despesa. A rota não filtra por data/conta.
    """
    return request("GET", '/transfers', params=payload(locals()))


@tool
def consultar_transferencia(transfer_group_id: str) -> dict[str, Any]:
    """
    Recebe transfer_group_id e retorna os dois lançamentos da transferência.
    API: GET /transfers/:groupId
    Uso: conferir origem, destino e valor antes de cancelar o par.
    """
    return request("GET", f"/transfers/{path_id(transfer_group_id)}")


@tool
def registrar_lancamento(
    description: str,
    amount: str,
    transaction_date: str,
    type: str,
    account_id: str | None = None,
    credit_card_id: str | None = None,
    category_id: str | None = None,
    status: str = "completed",
) -> dict[str, Any]:
    """
    Registra uma receita, despesa em conta ou compra no cartão.
    API: POST /transactions/create
    Dados: description, amount, transaction_date, type; account_id OU
    credit_card_id; category_id e status quando informados.
    type: income ou expense. status: pending, completed ou canceled.
    Uso: "Gastei 45 reais no almoço, pela conta Nubank."
    Cartão aceita apenas expense; fatura é definida pelo backend.
    Categoria deve corresponder ao tipo. Não usar esta ferramenta para
    transferências ou pagamentos de contas/faturas.
    Não assumir conta, data ou situação quando a mensagem for ambígua.
    """
    return request("POST", '/transactions/create', body=payload(locals()))


@tool
def atualizar_lancamento(
    transaction_id: str,
    description: str | None = None,
    amount: str | None = None,
    transaction_date: str | None = None,
    type: str | None = None,
    account_id: str | None = None,
    credit_card_id: str | None = None,
    category_id: str | None = None,
    status: str | None = None,
    remove_category: bool = False,
) -> dict[str, Any]:
    """
    Recebe ID e campos específicos para corrigir descrição, valor, data,
    categoria, origem ou situação. API: PATCH /transactions/update/:id
    Uso: "Aquele almoço foi 54 reais, não 45."
    Identificar o lançamento antes; respeitar as restrições de edição da API.
    Campos omitidos mantêm os valores atuais. remove_category remove a categoria.
    Ao informar só account_id ou credit_card_id, a origem anterior é removida.
    """
    data = payload(locals(), "transaction_id", "remove_category")
    if remove_category:
        if category_id is not None:
            return {"ok": False, "error": "Informe category_id ou remove_category, não os dois."}
        data["category_id"] = None
    if account_id is not None and credit_card_id is None:
        data["credit_card_id"] = None
    elif credit_card_id is not None and account_id is None:
        data["account_id"] = None
    return request("PATCH", f"/transactions/update/{path_id(transaction_id)}", body=data)


@tool
def excluir_lancamento(transaction_id: str) -> dict[str, Any]:
    """
    Recebe ID e solicita exclusão lógica. API: DELETE /transactions/:id
    Explicar qual registro será excluído e o efeito no saldo.
    Pagamentos gerados por bills/faturas e transferências têm regras próprias.
    """
    return request("DELETE", f"/transactions/{path_id(transaction_id)}")


@tool
def criar_conta_a_pagar(
    description: str,
    amount: str,
    due_date: str,
    category_id: str,
    account_id: str | None = None,
    recurrence: str = "none",
) -> dict[str, Any]:
    """
    Cadastra obrigação futura com descrição, valor, vencimento, categoria de
    despesa, conta opcional e recorrência opcional.
    recurrence: none, weekly, monthly ou yearly.
    API: POST /bills/create
    Uso: "Lembre que tenho internet de 100 reais para pagar dia 10."
    Cria a obrigação no app; não agenda notificação externa automaticamente.
    """
    return request("POST", '/bills/create', body=payload(locals()))


@tool
def atualizar_conta_a_pagar(
    bill_id: str,
    description: str | None = None,
    amount: str | None = None,
    due_date: str | None = None,
    category_id: str | None = None,
    account_id: str | None = None,
    recurrence: str | None = None,
    remove_account: bool = False,
) -> dict[str, Any]:
    """
    Recebe ID e alterações de valor, descrição, vencimento, conta, categoria
    ou recorrência. API: PATCH /bills/update/:id
    Uma conta já paga não pode ser editada por essa operação.
    Campos omitidos são preservados. remove_account remove a conta vinculada.
    """
    data = payload(locals(), "bill_id", "remove_account")
    if remove_account:
        if account_id is not None:
            return {"ok": False, "error": "Informe account_id ou remove_account, não os dois."}
        data["account_id"] = None
    return request("PATCH", f"/bills/update/{path_id(bill_id)}", body=data)


@tool
def excluir_conta_a_pagar(bill_id: str) -> dict[str, Any]:
    """
    Remove uma obrigação ainda não paga. API: DELETE /bills/:id
    Não representa estorno de um pagamento.
    """
    return request("DELETE", f"/bills/{path_id(bill_id)}")


@tool
def registrar_pagamento_conta(
    bill_id: str,
    transaction_date: str,
    account_id: str | None = None,
) -> dict[str, Any]:
    """
    Recebe ID da obrigação, data do pagamento e conta, se necessária.
    API: POST /bills/:id/pay
    Registra a quitação e a despesa juntas. Se recorrente, o backend cria a
    próxima ocorrência. Não criar outra despesa separadamente.
    Repetir a quitação da mesma obrigação não deve duplicar o pagamento.
    Isso registra pagamento no app; não paga boleto no banco real.
    """
    return request("POST", f"/bills/{path_id(bill_id)}/pay", body=payload(locals(), "bill_id"))


@tool
def fechar_fatura(invoice_id: str) -> dict[str, Any]:
    """
    Recebe ID e fecha uma fatura aberta. API: POST /invoices/:id/close
    Consultar compras pendentes antes: elas impedem o fechamento.
    Informar que as compras da fatura fechada deixam de ser editáveis.
    """
    return request("POST", f"/invoices/{path_id(invoice_id)}/close")


@tool
def registrar_pagamento_fatura(
    invoice_id: str,
    transaction_date: str,
    account_id: str | None = None,
) -> dict[str, Any]:
    """
    Recebe ID, conta de pagamento e data.
    API: POST /invoices/:id/pay
    Registra o pagamento integral de uma fatura fechada; o backend calcula
    o valor. Não enviar amount nem duplicar as despesas das compras.
    Pagamento parcial não é suportado. Não movimenta dinheiro no banco real.
    """
    return request("POST", f"/invoices/{path_id(invoice_id)}/pay", body=payload(locals(), "invoice_id"))


@tool
def registrar_transferencia(
    from_account_id: str,
    to_account_id: str,
    amount: str,
    transaction_date: str,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Recebe from_account_id, to_account_id, amount, transaction_date e descrição.
    API: POST /transfers/create
    Cria saída e entrada em uma única operação. Exige duas contas diferentes.
    Não criar os dois lançamentos separadamente nem alterar saldos manualmente.
    Uso: "Transferi 200 reais do banco para minha carteira."
    Apenas registra a movimentação no app; não executa Pix.
    """
    return request("POST", '/transfers/create', body=payload(locals()))


@tool
def cancelar_transferencia(transfer_group_id: str) -> dict[str, Any]:
    """
    Recebe transfer_group_id e cancela os dois lados juntos.
    API: DELETE /transfers/:groupId
    Consultar o par antes de cancelar; não excluir apenas uma das movimentações.
    """
    return request("DELETE", f"/transfers/{path_id(transfer_group_id)}")


@tool
def criar_conta(
    name: str,
    type: str,
    initial_balance: str = "0.00",
    is_active: bool = True,
) -> dict[str, Any]:
    """
    Cadastra nome, tipo e saldo inicial. API: POST /accounts/create
    Tipos: bank_account, cash, investment. Não representa abertura de conta real.
    """
    return request("POST", '/accounts/create', body=payload(locals()))


@tool
def atualizar_conta(
    account_id: str,
    name: str | None = None,
    type: str | None = None,
    initial_balance: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """
    Altera nome, tipo, saldo inicial ou is_active. API: PATCH /accounts/update/:id
    Desativar/reativar usa is_active. Alterar initial_balance muda a base do saldo;
    para registrar entradas/saídas normais, usar registrar_lancamento.
    """
    return request("PATCH", f"/accounts/update/{path_id(account_id)}", body=payload(locals(), "account_id"))


@tool
def criar_categoria(name: str, type: str) -> dict[str, Any]:
    """
    Cadastra nome e tipo income/expense. API: POST /categories/create
    Consultar as categorias existentes para evitar duplicação desnecessária.
    """
    return request("POST", '/categories/create', body=payload(locals()))


@tool
def atualizar_categoria(
    category_id: str,
    name: str | None = None,
    type: str | None = None,
) -> dict[str, Any]:
    """
    Altera nome/tipo. API: PATCH /categories/update/:id
    O backend impede mudar o tipo de uma categoria em uso.
    """
    return request("PATCH", f"/categories/update/{path_id(category_id)}", body=payload(locals(), "category_id"))


@tool
def excluir_categoria(category_id: str) -> dict[str, Any]:
    """
    Remove categoria sem vínculos. API: DELETE /categories/:id
    Se houver vínculos, explicar o impedimento retornado pela API.
    """
    return request("DELETE", f"/categories/{path_id(category_id)}")


@tool
def criar_cartao(
    name: str,
    payment_account_id: str,
    credit_limit: str,
    closing_day: int,
    due_day: int,
    is_active: bool = True,
) -> dict[str, Any]:
    """
    Cadastra nome, payment_account_id, credit_limit, closing_day e due_day.
    API: POST /credit-cards/create
    Precisa de conta de pagamento ativa; não solicita número, CVV ou senha.
    """
    return request("POST", '/credit-cards/create', body=payload(locals()))


@tool
def atualizar_cartao(
    credit_card_id: str,
    name: str | None = None,
    payment_account_id: str | None = None,
    credit_limit: str | None = None,
    closing_day: int | None = None,
    due_day: int | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """
    Atualiza cadastro ou is_active. API: PATCH /credit-cards/update/:id
    Depois da primeira fatura, fechamento/vencimento não podem mudar.
    """
    return request("PATCH", f"/credit-cards/update/{path_id(credit_card_id)}", body=payload(locals(), "credit_card_id"))


@tool
def criar_orcamento(category_id: str, amount_limit: str, year: int, month: int) -> dict[str, Any]:
    """
    Define category_id, amount_limit, year e month.
    API: POST /budgets/create
    Categoria deve ser de despesa; há um orçamento por categoria/mês/ano.
    Uso: "Quero limitar alimentação a 600 reais em outubro."
    """
    return request("POST", '/budgets/create', body=payload(locals()))


@tool
def atualizar_orcamento(
    budget_id: str,
    category_id: str | None = None,
    amount_limit: str | None = None,
    year: int | None = None,
    month: int | None = None,
) -> dict[str, Any]:
    """
    Recebe ID e altera limite, categoria ou período.
    API: PATCH /budgets/update/:id
    """
    return request("PATCH", f"/budgets/update/{path_id(budget_id)}", body=payload(locals(), "budget_id"))


@tool
def excluir_orcamento(budget_id: str) -> dict[str, Any]:
    """
    Remove o limite de planejamento. API: DELETE /budgets/:id
    Não exclui as despesas da categoria.
    """
    return request("DELETE", f"/budgets/{path_id(budget_id)}")


@tool
def comparar_meses(
    first_year: int,
    first_month: int,
    second_year: int,
    second_month: int,
) -> dict[str, Any]:
    """
    Consulta GET /insights/month-comparison para dois períodos e compara receitas, despesas e
    categorias. Retorna diferenças e percentuais, tratando base zero.
    Comparar income/expense/by_category; balance não é saldo histórico mensal.
    Os cálculos são feitos pelo Node.js. Percentual nulo significa base zero.
    """
    return request("GET", '/insights/month-comparison', params=payload(locals()))


@tool
def analisar_orcamento(year: int, month: int) -> dict[str, Any]:
    """
    Consulta GET /insights/budgets para identificar categorias acima do limite
    e valores restantes. Sugestões devem refletir os números reais.
    Inclui categorias sem orçamento e percentuais calculados no backend.
    """
    return request("GET", '/insights/budgets', params=payload(locals()))


@tool
def consultar_compromissos_do_periodo(start_date: str, end_date: str) -> dict[str, Any]:
    """
    Consulta GET /insights/commitments com start_date e end_date inclusivos.
    O backend reúne contas e faturas não pagas por vencimento, sem truncar a lista.
    Retorna obrigações e faturas identificadas separadamente, sem confundir
    essa previsão com despesas realizadas ou prometer saldo futuro garantido.
    """
    return request("GET", '/insights/commitments', params=payload(locals()))


# Ferramentas disponíveis ao modelo.
TOOLS = [
    consultar_resumo_financeiro,
    listar_contas,
    consultar_conta,
    listar_categorias,
    buscar_lancamentos,
    consultar_lancamento,
    listar_contas_a_pagar,
    consultar_conta_a_pagar,
    listar_cartoes,
    consultar_cartao,
    listar_faturas,
    consultar_fatura,
    listar_orcamentos,
    consultar_orcamento,
    listar_transferencias,
    consultar_transferencia,
    registrar_lancamento,
    atualizar_lancamento,
    excluir_lancamento,
    criar_conta_a_pagar,
    atualizar_conta_a_pagar,
    excluir_conta_a_pagar,
    registrar_pagamento_conta,
    fechar_fatura,
    registrar_pagamento_fatura,
    registrar_transferencia,
    cancelar_transferencia,
    criar_conta,
    atualizar_conta,
    criar_categoria,
    atualizar_categoria,
    excluir_categoria,
    criar_cartao,
    atualizar_cartao,
    criar_orcamento,
    atualizar_orcamento,
    excluir_orcamento,
    comparar_meses,
    analisar_orcamento,
    consultar_compromissos_do_periodo,
]
