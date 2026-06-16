"""
Testes do endpoint /carrinho da API ServeRest.
Fluxos cobertos: listar, adicionar (com/sem token, produto inexistente,
estoque insuficiente, carrinho duplicado), buscar por ID,
cancelar compra e concluir compra.
"""
import uuid
import pytest
import requests
import jsonschema

BASE_URL = "https://compassuol.serverest.dev"

# ─────────────────────────────────────────────
# JSON Schemas
# ─────────────────────────────────────────────

SCHEMA_ITEM_CARRINHO = {
    "type": "object",
    "required": ["idProduto", "quantidade", "precoUnitario"],
    "properties": {
        "idProduto":      {"type": "string"},
        "quantidade":     {"type": "integer"},
        "precoUnitario":  {"type": "integer"},
    },
}

SCHEMA_CARRINHO = {
    "type": "object",
    "required": ["produtos", "precoTotal", "quantidadeTotal", "idUsuario", "_id"],
    "properties": {
        "produtos":        {"type": "array", "items": SCHEMA_ITEM_CARRINHO},
        "precoTotal":      {"type": "integer"},
        "quantidadeTotal": {"type": "integer"},
        "idUsuario":       {"type": "string"},
        "_id":             {"type": "string"},
    },
    "additionalProperties": False,
}

SCHEMA_LISTA_CARRINHOS = {
    "type": "object",
    "required": ["quantidade", "carrinhos"],
    "properties": {
        "quantidade": {"type": "integer"},
        "carrinhos":  {"type": "array", "items": SCHEMA_CARRINHO},
    },
}


# ─────────────────────────────────────────────
# Fixtures locais
# ─────────────────────────────────────────────

def email_unico():
    return f"qa_{uuid.uuid4().hex[:8]}@teste.com"


def nome_produto_unico():
    return f"Prod Carrinho {uuid.uuid4().hex[:6]}"


@pytest.fixture
def usuario_com_token():
    """Cria um usuário comum exclusivo para testes de carrinho e retorna dados + token."""
    payload = {
        "nome": "Carrinho Tester",
        "email": email_unico(),
        "password": "senha123",
        "administrador": "false",
    }
    resp = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp.status_code == 201, f"Falha ao criar usuário: {resp.text}"
    usuario_id = resp.json()["_id"]

    login = requests.post(
        f"{BASE_URL}/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, f"Falha no login: {login.text}"
    token = login.json()["authorization"]

    yield {"_id": usuario_id, "token": token, **payload}

    requests.delete(f"{BASE_URL}/carrinho/cancelar-compra", headers={"Authorization": token})
    requests.delete(f"{BASE_URL}/usuarios/{usuario_id}")


@pytest.fixture
def produto_em_estoque(headers_admin):
    """Cria um produto com estoque disponível para testes de carrinho."""
    payload = {
        "nome": nome_produto_unico(),
        "preco": 50,
        "descricao": "Produto para carrinho",
        "quantidade": 20,
    }
    resp = requests.post(f"{BASE_URL}/produtos", json=payload, headers=headers_admin)
    assert resp.status_code == 201, f"Falha ao criar produto: {resp.text}"
    produto_id = resp.json()["_id"]
    yield {**payload, "_id": produto_id}
    requests.delete(f"{BASE_URL}/produtos/{produto_id}", headers=headers_admin)


@pytest.fixture
def carrinho_criado(usuario_com_token, produto_em_estoque):
    """Cria um carrinho com um produto e retorna os dados do carrinho."""
    headers = {"Authorization": usuario_com_token["token"]}
    payload = {
        "produtos": [
            {"idProduto": produto_em_estoque["_id"], "quantidade": 2}
        ]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload, headers=headers)
    assert resp.status_code == 201, f"Falha ao criar carrinho: {resp.text}"
    carrinho_id = resp.json()["_id"]
    yield {"_id": carrinho_id, "usuario": usuario_com_token, "produto": produto_em_estoque}


# ─────────────────────────────────────────────
# GET /carrinho
# ─────────────────────────────────────────────

@pytest.mark.carrinho
def test_listar_carrinhos_retorna_200():
    """Listar todos os carrinhos deve retornar HTTP 200."""
    resp = requests.get(f"{BASE_URL}/carrinho")
    assert resp.status_code == 200


@pytest.mark.carrinho
def test_listar_carrinhos_schema_valido():
    """Resposta de listagem deve seguir o schema de lista de carrinhos. (JSON Schema)"""
    resp = requests.get(f"{BASE_URL}/carrinho")
    jsonschema.validate(instance=resp.json(), schema=SCHEMA_LISTA_CARRINHOS)


@pytest.mark.carrinho
def test_listar_carrinhos_quantidade_coerente():
    """O campo 'quantidade' deve corresponder ao tamanho da lista retornada."""
    resp = requests.get(f"{BASE_URL}/carrinho")
    body = resp.json()
    assert body["quantidade"] == len(body["carrinhos"])


# ─────────────────────────────────────────────
# POST /carrinho
# ─────────────────────────────────────────────

@pytest.mark.carrinho
def test_criar_carrinho_com_token_valido(usuario_com_token, produto_em_estoque):
    """Criar carrinho com token válido e produto existente deve retornar 201."""
    headers = {"Authorization": usuario_com_token["token"]}
    payload = {
        "produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": 1}]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert "message" in body
    assert "_id" in body
    assert body["message"] == "Cadastro realizado com sucesso"


@pytest.mark.carrinho
def test_criar_carrinho_sem_token(produto_em_estoque):
    """Criar carrinho sem token de autorização deve retornar 401."""
    payload = {
        "produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": 1}]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload)
    assert resp.status_code == 401
    assert "Token de acesso ausente" in resp.json().get("message", "")


@pytest.mark.carrinho
def test_criar_carrinho_produto_inexistente(usuario_com_token):
    """Criar carrinho com idProduto inexistente deve retornar 400."""
    headers = {"Authorization": usuario_com_token["token"]}
    payload = {
        "produtos": [{"idProduto": "id_produto_fantasma_xyz", "quantidade": 1}]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Produto não encontrado" in resp.json().get("message", "")


@pytest.mark.carrinho
def test_criar_carrinho_quantidade_maior_que_estoque(usuario_com_token, produto_em_estoque):
    """Criar carrinho com quantidade superior ao estoque disponível deve retornar 400."""
    headers = {"Authorization": usuario_com_token["token"]}
    payload = {
        "produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": 9999}]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload, headers=headers)
    assert resp.status_code == 400
    body = resp.json()
    assert "insuficiente" in body.get("message", "").lower() or "estoque" in body.get("message", "").lower()


@pytest.mark.carrinho
def test_criar_carrinho_duplicado_mesmo_usuario(carrinho_criado, produto_em_estoque):
    """Usuário com carrinho já existente não pode criar um segundo — deve retornar 400."""
    headers = {"Authorization": carrinho_criado["usuario"]["token"]}
    payload = {
        "produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": 1}]
    }
    resp = requests.post(f"{BASE_URL}/carrinho", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Não é permitido ter mais de 1 carrinho" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# GET /carrinho/{_id}
# ─────────────────────────────────────────────

@pytest.mark.carrinho
def test_buscar_carrinho_por_id_valido(carrinho_criado):
    """Buscar carrinho por _id existente deve retornar 200 e schema correto. (JSON Schema)"""
    resp = requests.get(f"{BASE_URL}/carrinho/{carrinho_criado['_id']}")
    assert resp.status_code == 200
    jsonschema.validate(instance=resp.json(), schema=SCHEMA_CARRINHO)


@pytest.mark.carrinho
def test_buscar_carrinho_por_id_inexistente():
    """Buscar carrinho com _id inexistente deve retornar 400."""
    resp = requests.get(f"{BASE_URL}/carrinho/id_carrinho_fantasma")
    assert resp.status_code == 400
    assert "Carrinho não encontrado" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# DELETE /carrinho/cancelar-compra
# ─────────────────────────────────────────────

@pytest.mark.carrinho
def test_cancelar_compra_devolve_estoque(usuario_com_token, produto_em_estoque):
    """Cancelar compra deve retornar 200 e o estoque do produto deve ser restaurado."""
    headers = {"Authorization": usuario_com_token["token"]}

    estoque_antes = requests.get(f"{BASE_URL}/produtos/{produto_em_estoque['_id']}").json()["quantidade"]

    quantidade_comprada = 3
    requests.post(
        f"{BASE_URL}/carrinho",
        json={"produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": quantidade_comprada}]},
        headers=headers,
    )

    resp_cancel = requests.delete(f"{BASE_URL}/carrinho/cancelar-compra", headers=headers)
    assert resp_cancel.status_code == 200
    assert "Registro excluído com sucesso" in resp_cancel.json().get("message", "")

    estoque_depois = requests.get(f"{BASE_URL}/produtos/{produto_em_estoque['_id']}").json()["quantidade"]
    assert estoque_depois == estoque_antes


@pytest.mark.carrinho
def test_cancelar_compra_sem_carrinho(usuario_com_token):
    """Cancelar compra de usuário sem carrinho deve retornar 200 com aviso."""
    headers = {"Authorization": usuario_com_token["token"]}
    resp = requests.delete(f"{BASE_URL}/carrinho/cancelar-compra", headers=headers)
    assert resp.status_code == 200
    assert "Não foi encontrado carrinho" in resp.json().get("message", "")


@pytest.mark.carrinho
def test_cancelar_compra_sem_token():
    """Cancelar compra sem token deve retornar 401."""
    resp = requests.delete(f"{BASE_URL}/carrinho/cancelar-compra")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# DELETE /carrinho/concluir-compra
# ─────────────────────────────────────────────

@pytest.mark.carrinho
def test_concluir_compra_remove_carrinho(usuario_com_token, produto_em_estoque):
    """Concluir compra deve retornar 200 e remover o carrinho sem restaurar estoque."""
    headers = {"Authorization": usuario_com_token["token"]}

    estoque_antes = requests.get(f"{BASE_URL}/produtos/{produto_em_estoque['_id']}").json()["quantidade"]
    quantidade_comprada = 2

    requests.post(
        f"{BASE_URL}/carrinho",
        json={"produtos": [{"idProduto": produto_em_estoque["_id"], "quantidade": quantidade_comprada}]},
        headers=headers,
    )

    resp_concluir = requests.delete(f"{BASE_URL}/carrinho/concluir-compra", headers=headers)
    assert resp_concluir.status_code == 200
    assert "Registro excluído com sucesso" in resp_concluir.json().get("message", "")

    estoque_depois = requests.get(f"{BASE_URL}/produtos/{produto_em_estoque['_id']}").json()["quantidade"]
    assert estoque_depois == estoque_antes - quantidade_comprada


@pytest.mark.carrinho
def test_concluir_compra_sem_carrinho(usuario_com_token):
    """Concluir compra de usuário sem carrinho deve retornar 200 com aviso."""
    headers = {"Authorization": usuario_com_token["token"]}
    resp = requests.delete(f"{BASE_URL}/carrinho/concluir-compra", headers=headers)
    assert resp.status_code == 200
    assert "Não foi encontrado carrinho" in resp.json().get("message", "")


@pytest.mark.carrinho
def test_concluir_compra_sem_token():
    """Concluir compra sem token deve retornar 401."""
    resp = requests.delete(f"{BASE_URL}/carrinho/concluir-compra")
    assert resp.status_code == 401
