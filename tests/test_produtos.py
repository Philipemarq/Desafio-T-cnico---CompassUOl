"""
Testes do endpoint /produtos da API ServeRest.
Parte 2: listagem, criação (com/sem token admin), busca, atualização e exclusão.
Inclui validação de JSON Schema em 3 endpoints (Extra 1).
"""
import uuid
import pytest
import requests
import jsonschema

BASE_URL = "https://compassuol.serverest.dev"

# ─────────────────────────────────────────────
# JSON Schemas
# ─────────────────────────────────────────────

SCHEMA_PRODUTO = {
    "type": "object",
    "required": ["nome", "preco", "descricao", "quantidade", "_id"],
    "properties": {
        "nome":        {"type": "string"},
        "preco":       {"type": "number"},
        "descricao":   {"type": "string"},
        "quantidade":  {"type": "integer"},
        "_id":         {"type": "string"},
    },
    "additionalProperties": False,
}

SCHEMA_LISTA_PRODUTOS = {
    "type": "object",
    "required": ["quantidade", "produtos"],
    "properties": {
        "quantidade": {"type": "integer"},
        "produtos": {
            "type": "array",
            "items": SCHEMA_PRODUTO,
        },
    },
}

SCHEMA_CRIACAO_PRODUTO = {
    "type": "object",
    "required": ["message", "_id"],
    "properties": {
        "message": {"type": "string"},
        "_id":     {"type": "string"},
    },
}


def nome_produto_unico():
    return f"Produto QA {uuid.uuid4().hex[:6]}"


# ─────────────────────────────────────────────
# GET /produtos
# ─────────────────────────────────────────────

@pytest.mark.produtos
def test_listar_produtos_retorna_200():
    """Listar todos os produtos deve retornar HTTP 200."""
    resp = requests.get(f"{BASE_URL}/produtos")
    assert resp.status_code == 200


@pytest.mark.produtos
def test_listar_produtos_schema_valido():
    """Resposta de listagem deve seguir o schema de lista de produtos. (Extra 1)"""
    resp = requests.get(f"{BASE_URL}/produtos")
    jsonschema.validate(instance=resp.json(), schema=SCHEMA_LISTA_PRODUTOS)


@pytest.mark.produtos
def test_listar_produtos_quantidade_coerente():
    """O campo 'quantidade' deve corresponder ao tamanho da lista retornada."""
    resp = requests.get(f"{BASE_URL}/produtos")
    body = resp.json()
    assert body["quantidade"] == len(body["produtos"])


# ─────────────────────────────────────────────
# POST /produtos — com token de admin
# ─────────────────────────────────────────────

@pytest.mark.produtos
def test_cadastrar_produto_com_token_admin(headers_admin):
    """Cadastrar produto com token de admin válido deve retornar 201. (Extra 1)"""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 99,
        "descricao": "Produto de teste automatizado",
        "quantidade": 10,
    }
    resp = requests.post(f"{BASE_URL}/produtos", json=payload, headers=headers_admin)
    assert resp.status_code == 201
    body = resp.json()
    jsonschema.validate(instance=body, schema=SCHEMA_CRIACAO_PRODUTO)
    assert body["message"] == "Cadastro realizado com sucesso"
    requests.delete(f"{BASE_URL}/produtos/{body['_id']}", headers=headers_admin)


@pytest.mark.produtos
def test_cadastrar_produto_sem_token():
    """Cadastrar produto sem token de autorização deve retornar 401."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 50,
        "descricao": "Sem auth",
        "quantidade": 5,
    }
    resp = requests.post(f"{BASE_URL}/produtos", json=payload)
    assert resp.status_code == 401
    assert "Token de acesso ausente" in resp.json().get("message", "")


@pytest.mark.produtos
def test_cadastrar_produto_nome_duplicado(headers_admin):
    """Cadastrar dois produtos com o mesmo nome deve retornar 400 na segunda tentativa."""
    nome = nome_produto_unico()
    payload = {
        "nome": nome,
        "preco": 20,
        "descricao": "Duplicado",
        "quantidade": 1,
    }
    resp1 = requests.post(f"{BASE_URL}/produtos", json=payload, headers=headers_admin)
    assert resp1.status_code == 201
    produto_id = resp1.json()["_id"]

    resp2 = requests.post(f"{BASE_URL}/produtos", json=payload, headers=headers_admin)
    assert resp2.status_code == 400
    assert "Já existe produto com esse nome" in resp2.json().get("message", "")

    requests.delete(f"{BASE_URL}/produtos/{produto_id}", headers=headers_admin)


@pytest.mark.produtos
def test_cadastrar_produto_token_usuario_nao_admin(usuario_criado, base_url):
    """Cadastrar produto com token de usuário não-admin deve retornar 403."""
    login_resp = requests.post(
        f"{base_url}/login",
        json={"email": usuario_criado["email"], "password": usuario_criado["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["authorization"]

    payload = {
        "nome": nome_produto_unico(),
        "preco": 30,
        "descricao": "Usuário não admin",
        "quantidade": 2,
    }
    resp = requests.post(
        f"{BASE_URL}/produtos", json=payload, headers={"Authorization": token}
    )
    assert resp.status_code == 403
    assert "administrador" in resp.json().get("message", "").lower()


# ─────────────────────────────────────────────
# GET /produtos/{_id}
# ─────────────────────────────────────────────

@pytest.fixture
def produto_criado(headers_admin):
    """Cria um produto de teste e remove ao finalizar."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 75,
        "descricao": "Produto fixture",
        "quantidade": 3,
    }
    resp = requests.post(f"{BASE_URL}/produtos", json=payload, headers=headers_admin)
    assert resp.status_code == 201
    produto_id = resp.json()["_id"]
    yield {**payload, "_id": produto_id}
    requests.delete(f"{BASE_URL}/produtos/{produto_id}", headers=headers_admin)


@pytest.mark.produtos
def test_buscar_produto_por_id_valido(produto_criado):
    """Buscar produto por _id existente deve retornar 200 e schema válido. (Extra 1)"""
    resp = requests.get(f"{BASE_URL}/produtos/{produto_criado['_id']}")
    assert resp.status_code == 200
    jsonschema.validate(instance=resp.json(), schema=SCHEMA_PRODUTO)


@pytest.mark.produtos
def test_buscar_produto_por_id_inexistente():
    """Buscar produto com _id inexistente deve retornar 400."""
    resp = requests.get(f"{BASE_URL}/produtos/id_que_nao_existe")
    assert resp.status_code == 400
    assert "Produto não encontrado" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# PUT /produtos/{_id}
# ─────────────────────────────────────────────

@pytest.mark.produtos
def test_atualizar_produto_valido(produto_criado, headers_admin):
    """Atualizar produto existente com token admin deve retornar 200."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 120,
        "descricao": "Descrição atualizada",
        "quantidade": 8,
    }
    resp = requests.put(
        f"{BASE_URL}/produtos/{produto_criado['_id']}",
        json=payload,
        headers=headers_admin,
    )
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.produtos
def test_atualizar_produto_sem_token(produto_criado):
    """Atualizar produto sem token deve retornar 401."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 10,
        "descricao": "Sem auth",
        "quantidade": 1,
    }
    resp = requests.put(f"{BASE_URL}/produtos/{produto_criado['_id']}", json=payload)
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# DELETE /produtos/{_id}
# ─────────────────────────────────────────────

@pytest.mark.produtos
def test_excluir_produto_existente(headers_admin):
    """Excluir produto existente com token admin deve retornar 200."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 5,
        "descricao": "Para deletar",
        "quantidade": 1,
    }
    resp_create = requests.post(
        f"{BASE_URL}/produtos", json=payload, headers=headers_admin
    )
    assert resp_create.status_code == 201
    produto_id = resp_create.json()["_id"]

    resp_del = requests.delete(
        f"{BASE_URL}/produtos/{produto_id}", headers=headers_admin
    )
    assert resp_del.status_code == 200
    assert "Registro excluído com sucesso" in resp_del.json().get("message", "")


@pytest.mark.produtos
def test_excluir_produto_inexistente(headers_admin):
    """Excluir produto com _id inexistente deve retornar 200 com aviso."""
    resp = requests.delete(
        f"{BASE_URL}/produtos/id_nao_existe_000", headers=headers_admin
    )
    assert resp.status_code == 200
    assert "Nenhum registro excluído" in resp.json().get("message", "")


@pytest.mark.produtos
def test_excluir_produto_sem_token(produto_criado):
    """Excluir produto sem token deve retornar 401."""
    resp = requests.delete(f"{BASE_URL}/produtos/{produto_criado['_id']}")
    assert resp.status_code == 401
