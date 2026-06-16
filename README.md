# ServeRest API — Suíte de Testes Automatizados

Testes em **Python + Pytest** para a API pública [ServeRest](https://compassuol.serverest.dev/),
cobrindo os endpoints de **Usuários**, **Login**, **Produtos** e **Carrinho**.

---

## Melhorias aplicadas em relação à Versão 1 (Parte 1 → Parte 2)

| # | Melhoria | Detalhe |
|---|----------|---------|
| 1 | **Expansão de cobertura** | Adicionados módulos de Login, Produtos e Carrinho, elevando de 14 para 51 testes. |
| 2 | **Plano de testes formal** | Arquivo `PLANO-DE-TESTES.md` documenta objetivo, estratégia, escopo, cenários e critérios de qualidade antes da implementação. |
| 3 | **Fixtures reutilizáveis com teardown** | `conftest.py` centraliza criação de usuários, admin e token; cada fixture remove seus dados ao final, garantindo isolamento real. |
| 4 | **Validação de JSON Schema** | `jsonschema` valida a estrutura das respostas de 5 endpoints, detectando mudanças não documentadas no contrato. |
| 5 | **Fluxo de compra de ponta a ponta** | Testes de Carrinho cobrem o ciclo completo: admin cria produto → usuário faz login → adiciona ao carrinho → cancela (verifica devolução de estoque) ou conclui (verifica desconto de estoque). |
| 6 | **Análise de cobertura documentada** | README inclui cálculo formal de cobertura com base no método de endpoints × verbos × cenários (ver seção abaixo). |
| 7 | **Relatório HTML** | `pytest-html` instalado; execute com `--html=report.html` para gerar relatório visual. |
| 8 | **Marcadores Pytest** | `@pytest.mark.usuarios`, `@pytest.mark.login`, `@pytest.mark.produtos`, `@pytest.mark.carrinho` permitem execução seletiva por módulo. |

---

## Pré-requisitos

- Python 3.11 ou superior
- pip / virtualenv

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd serverest-tests

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## Como Rodar

### Todos os testes
```bash
pytest
```

### Por módulo
```bash
pytest -m usuarios    # Apenas testes de Usuários
pytest -m login       # Apenas testes de Login
pytest -m produtos    # Apenas testes de Produtos
pytest -m carrinho    # Apenas testes de Carrinho
```

### Com relatório HTML
```bash
pytest --html=report.html --self-contained-html
```

### Saída detalhada
```bash
pytest -v
```

---

## Estrutura do Projeto

```
serverest-tests/
├── tests/
│   ├── conftest.py          # Fixtures compartilhadas (usuário, admin, token)
│   ├── test_usuarios.py     # 14 testes — endpoint /usuarios
│   ├── test_login.py        #  7 testes — endpoint /login
│   ├── test_produtos.py     # 14 testes — endpoint /produtos
│   └── test_carrinho.py     # 16 testes — endpoint /carrinho
├── requirements.txt
├── pytest.ini
├── PLANO-DE-TESTES.md
└── README.md
```

---

## Análise de Cobertura

### Método utilizado

Baseado no artigo [*Como verificar a cobertura de testes da API REST*](https://medium.com/revista-dtar/como-verificar-a-cobertura-de-testes-da-api-rest-9e2f745564b),
a cobertura foi calculada pela fórmula:

```
Cobertura = (Cenários testados / Cenários possíveis identificados) × 100
```

Os cenários possíveis foram levantados a partir da documentação Swagger da ServeRest,
considerando: endpoints documentados × verbos HTTP × combinações de entrada (válido/inválido/campos faltando).

### Cobertura por endpoint

| Endpoint                            | Cenários possíveis | Cenários testados | Cobertura |
|-------------------------------------|--------------------|-------------------|-----------|
| `POST /login`                       | 7                  | 7                 | 100%      |
| `GET /usuarios`                     | 3                  | 3                 | 100%      |
| `POST /usuarios`                    | 5                  | 5                 | 100%      |
| `GET /usuarios/{id}`                | 2                  | 2                 | 100%      |
| `PUT /usuarios/{id}`                | 2                  | 2                 | 100%      |
| `DELETE /usuarios/{id}`             | 2                  | 2                 | 100%      |
| `GET /produtos`                     | 3                  | 3                 | 100%      |
| `POST /produtos`                    | 4                  | 4                 | 100%      |
| `GET /produtos/{id}`                | 2                  | 2                 | 100%      |
| `PUT /produtos/{id}`                | 2                  | 2                 | 100%      |
| `DELETE /produtos/{id}`             | 3                  | 3                 | 100%      |
| `GET /carrinho`                     | 3                  | 3                 | 100%      |
| `POST /carrinho`                    | 5                  | 5                 | 100%      |
| `GET /carrinho/{id}`                | 2                  | 2                 | 100%      |
| `DELETE /carrinho/cancelar-compra`  | 3                  | 3                 | 100%      |
| `DELETE /carrinho/concluir-compra`  | 3                  | 3                 | 100%      |
| **Total**                           | **51**             | **51**            | **100%**  |

> **Cobertura total atingida: 100%** dos cenários planejados no escopo definido.

### Cenários fora do escopo e motivo

| Cenário                                         | Motivo                                                    |
|-------------------------------------------------|-----------------------------------------------------------|
| Testes de performance / carga                   | Requerem ferramentas dedicadas (k6, Locust, JMeter)       |
| Testes de segurança (SQL injection, XSS)        | Fora do escopo funcional desta suíte                      |
| Campos com tipos inválidos (ex: `preco: "abc"`) | API não retorna erro de tipo — aceita strings como número |
| Filtros e busca via query params                | Comportamento não é consistente o suficiente para assertar|

---

## Reporte de Bug

Durante a execução dos testes foi identificado o seguinte comportamento inesperado na API:

### Bug identificado: `DELETE /usuarios/{id}` e `DELETE /produtos/{id}` retornam HTTP 200 para IDs inexistentes

**Passos para reproduzir:**
```bash
DELETE https://compassuol.serverest.dev/usuarios/id_qualquer_que_nao_existe
```

**Resultado esperado:** HTTP `404 Not Found` (recurso não encontrado).

**Resultado obtido:** HTTP `200 OK` com body `{"message": "Nenhum registro excluído"}`.

**Severidade:** Baixa — não impede o uso da API, mas viola o padrão REST (RFC 7231) e
pode mascarar erros em clientes que verificam apenas o status code.

> Reporte completo deve ser aberto como **Issue** no repositório GitHub seguindo o template:
> *Título, Passos para reproduzir, Comportamento esperado, Comportamento obtido, Severidade, Evidências (screenshot/log).*

---

## Dependências

| Pacote        | Versão  | Uso                                     |
|---------------|---------|-----------------------------------------|
| pytest        | 8.3.5   | Framework de testes                     |
| requests      | 2.32.3  | Chamadas HTTP à API                     |
| jsonschema    | 4.23.0  | Validação de estrutura das respostas    |
| pytest-html   | 4.1.1   | Geração de relatório HTML               |
| faker         | 33.1.0  | Geração de dados falsos (disponível para expansões futuras) |
