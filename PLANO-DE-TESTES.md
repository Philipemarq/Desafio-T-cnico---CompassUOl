# Plano de Testes — ServeRest API

> Documento criado antes da evolução do código (Parte 2) e atualizado conforme o desafio avançou.

---

## 1. Objetivo da Suíte

Validar o comportamento dos endpoints públicos da API ServeRest
(`https://compassuol.serverest.dev/`) nos fluxos de Usuários, Login, Produtos e Carrinho,
garantindo que respostas de sucesso e erro sigam os contratos documentados e que
fluxos de autenticação e ciclo de vida de compra funcionem corretamente de ponta a ponta.

---

## 2. Estratégia

| Dimensão       | Escolha                                                                 |
|----------------|-------------------------------------------------------------------------|
| Tipo de teste  | Testes de API (caixa-preta, camada HTTP)                                |
| Camada         | Integração — chamadas reais contra o servidor de homologação            |
| Ferramentas    | Python 3.11+, Pytest 8, Requests, jsonschema, Faker/uuid                |
| Isolamento     | Cada teste cria e limpa seus próprios dados (fixtures com teardown)     |
| Paralelismo    | Testes independentes entre si; sem dependência de ordem de execução     |
| CI             | Compatível com GitHub Actions (`pytest --tb=short`)                     |

---

## 3. Escopo

### Coberto

| Endpoint              | Operações cobertas                                              |
|-----------------------|-----------------------------------------------------------------|
| `POST /login`         | Credenciais válidas, senha errada, e-mail inexistente, campos vazios |
| `GET /usuarios`       | Listagem, validação de quantidade, schema JSON                  |
| `POST /usuarios`      | Cadastro válido, e-mail duplicado, campos obrigatórios faltando |
| `GET /usuarios/{id}`  | Busca por ID existente e inexistente                            |
| `PUT /usuarios/{id}`  | Atualização válida, ID inexistente                              |
| `DELETE /usuarios/{id}` | Exclusão existente e inexistente                             |
| `GET /produtos`       | Listagem, validação de quantidade, schema JSON                  |
| `POST /produtos`      | Com token admin, sem token, duplicado, usuário não-admin        |
| `GET /produtos/{id}`  | Busca por ID existente e inexistente                            |
| `PUT /produtos/{id}`  | Atualização com e sem token                                     |
| `DELETE /produtos/{id}` | Exclusão com e sem token, ID inexistente                     |
| `GET /carrinho`       | Listagem, schema JSON, validação de quantidade                  |
| `POST /carrinho`      | Com token, sem token, produto inexistente, estoque insuficiente, duplicado |
| `GET /carrinho/{id}`  | Busca por ID existente e inexistente, schema JSON               |
| `DELETE /carrinho/cancelar-compra` | Com token (verifica devolução de estoque), sem carrinho, sem token |
| `DELETE /carrinho/concluir-compra` | Com token (verifica estoque não restaurado), sem carrinho, sem token |

### Fora do Escopo (e por quê)

| Endpoint/Cenário                       | Motivo da exclusão                                       |
|----------------------------------------|----------------------------------------------------------|
| Testes de performance/carga            | Requerem ferramentas dedicadas (k6, Locust)              |
| Testes de segurança (injeção)          | Fora do escopo funcional desta suíte                     |
| Paginação / filtros avançados          | API não documenta parâmetros de paginação formalmente    |

---

## 4. Cenários a Implementar

### 4.1 Usuários (`tests/test_usuarios.py`)

- [x] `test_listar_usuarios_retorna_200`
- [x] `test_listar_usuarios_estrutura_json`
- [x] `test_listar_usuarios_quantidade_coerente`
- [x] `test_cadastrar_usuario_valido`
- [x] `test_cadastrar_usuario_email_duplicado`
- [x] `test_cadastrar_usuario_sem_nome`
- [x] `test_cadastrar_usuario_sem_email`
- [x] `test_cadastrar_usuario_sem_password`
- [x] `test_buscar_usuario_por_id_valido`
- [x] `test_buscar_usuario_por_id_inexistente`
- [x] `test_atualizar_usuario_valido`
- [x] `test_atualizar_usuario_id_inexistente`
- [x] `test_excluir_usuario_existente`
- [x] `test_excluir_usuario_inexistente`

### 4.2 Login (`tests/test_login.py`)

- [x] `test_login_credenciais_validas`
- [x] `test_login_retorna_token_nao_vazio`
- [x] `test_login_senha_errada`
- [x] `test_login_email_inexistente`
- [x] `test_login_sem_email`
- [x] `test_login_sem_password`
- [x] `test_login_body_vazio`

### 4.3 Produtos (`tests/test_produtos.py`)

- [x] `test_listar_produtos_retorna_200`
- [x] `test_listar_produtos_schema_valido` *(JSON Schema — Extra 1)*
- [x] `test_listar_produtos_quantidade_coerente`
- [x] `test_cadastrar_produto_com_token_admin` *(JSON Schema — Extra 1)*
- [x] `test_cadastrar_produto_sem_token`
- [x] `test_cadastrar_produto_nome_duplicado`
- [x] `test_cadastrar_produto_token_usuario_nao_admin`
- [x] `test_buscar_produto_por_id_valido` *(JSON Schema — Extra 1)*
- [x] `test_buscar_produto_por_id_inexistente`
- [x] `test_atualizar_produto_valido`
- [x] `test_atualizar_produto_sem_token`
- [x] `test_excluir_produto_existente`
- [x] `test_excluir_produto_inexistente`
- [x] `test_excluir_produto_sem_token`

### 4.4 Carrinho (`tests/test_carrinho.py`)

- [x] `test_listar_carrinhos_retorna_200`
- [x] `test_listar_carrinhos_schema_valido` *(JSON Schema)*
- [x] `test_listar_carrinhos_quantidade_coerente`
- [x] `test_criar_carrinho_com_token_valido`
- [x] `test_criar_carrinho_sem_token`
- [x] `test_criar_carrinho_produto_inexistente`
- [x] `test_criar_carrinho_quantidade_maior_que_estoque`
- [x] `test_criar_carrinho_duplicado_mesmo_usuario`
- [x] `test_buscar_carrinho_por_id_valido` *(JSON Schema)*
- [x] `test_buscar_carrinho_por_id_inexistente`
- [x] `test_cancelar_compra_devolve_estoque`
- [x] `test_cancelar_compra_sem_carrinho`
- [x] `test_cancelar_compra_sem_token`
- [x] `test_concluir_compra_remove_carrinho`
- [x] `test_concluir_compra_sem_carrinho`
- [x] `test_concluir_compra_sem_token`

---

## 5. Critérios de Qualidade

Um teste está **pronto** quando:

1. **Nome descritivo** — lendo o nome, qualquer pessoa entende o que está sendo validado, sem precisar ler o código.
2. **Independente** — não depende de outro teste ter rodado antes; cria e limpa seus próprios dados.
3. **Assert específico** — verifica ao menos o status HTTP **e** um campo relevante do body (mensagem, ID ou estrutura).
4. **E-mail dinâmico** — usa `uuid` ou `Faker` para evitar conflito de dados entre execuções.
5. **Sem side-effects** — dados criados no teste são removidos no teardown (fixture ou chamada explícita de delete).
6. **Rápido** — não faz esperas artificiais (`time.sleep`) sem justificativa documentada.
