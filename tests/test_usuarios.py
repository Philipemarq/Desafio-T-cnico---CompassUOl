"""
Testes do endpoint /usuarios da API ServeRest.
Parte 1: cobertura mínima de 10 testes com cenários de CRUD completo.
"""
import uuid
import pytest
import requests
import jsonschema

BASE_URL = "https://compassuol.serverest.dev"

SCHEMA_USUARIO = {
    "type": "object",
    "required": ["nome", "email", "password", "administrador", "_id"],
    "properties": {
        "nome":          {"type": "string"},
        "email":         {"type": "string"},
        "password":      {"type": "string"},
        "administrador": {"type": "string"},
        "_id":           {"type": "string"},
    },
    "additionalProperties": False,
}

SCHEMA_LISTA_USUARIOS = {
    "type": "object",
    "required": ["quantidade", "usuarios"],
    "properties": {
        "quantidade": {"type": "integer"},
        "usuarios": {
            "type": "array",
            "items": SCHEMA_USUARIO,
        },
    },
}


def email_unico():
    return f"qa_{uuid.uuid4().hex[:8]}@teste.com"


# ─────────────────────────────────────────────
# GET /usuarios
# ─────────────────────────────────────────────

@pytest.mark.usuarios
def test_listar_usuarios_retorna_200():
    """Listar todos os usuários deve retornar HTTP 200."""
    resp = requests.get(f"{BASE_URL}/usuarios")
    assert resp.status_code == 200


@pytest.mark.usuarios
def test_listar_usuarios_estrutura_json():
    """Resposta de listagem deve ter 'quantidade' (int) e 'usuarios' (lista)."""
    resp = requests.get(f"{BASE_URL}/usuarios")
    body = resp.json()
    jsonschema.validate(instance=body, schema=SCHEMA_LISTA_USUARIOS)


@pytest.mark.usuarios
def test_listar_usuarios_quantidade_coerente():
    """O campo 'quantidade' deve corresponder ao tamanho da lista retornada."""
    resp = requests.get(f"{BASE_URL}/usuarios")
    body = resp.json()
    assert body["quantidade"] == len(body["usuarios"])


# ─────────────────────────────────────────────
# POST /usuarios
# ─────────────────────────────────────────────

@pytest.mark.usuarios
def test_cadastrar_usuario_valido():
    """Cadastrar usuário com dados válidos deve retornar 201 e _id."""
    payload = {
        "nome": "QA Tester",
        "email": email_unico(),
        "password": "senha123",
        "administrador": "false",
    }
    resp = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert "message" in body
    assert "_id" in body
    assert body["message"] == "Cadastro realizado com sucesso"
    requests.delete(f"{BASE_URL}/usuarios/{body['_id']}")


@pytest.mark.usuarios
def test_cadastrar_usuario_email_duplicado():
    """Tentar cadastrar dois usuários com o mesmo e-mail deve retornar 400."""
    email = email_unico()
    payload = {
        "nome": "QA Duplicado",
        "email": email,
        "password": "senha123",
        "administrador": "false",
    }
    resp1 = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp1.status_code == 201
    usuario_id = resp1.json()["_id"]

    resp2 = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp2.status_code == 400
    assert "Este email já está sendo usado" in resp2.json().get("message", "")

    requests.delete(f"{BASE_URL}/usuarios/{usuario_id}")


@pytest.mark.usuarios
def test_cadastrar_usuario_sem_nome():
    """Omitir o campo 'nome' deve retornar 400."""
    payload = {
        "email": email_unico(),
        "password": "senha123",
        "administrador": "false",
    }
    resp = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp.status_code == 400
    assert "nome" in resp.json()


@pytest.mark.usuarios
def test_cadastrar_usuario_sem_email():
    """Omitir o campo 'email' deve retornar 400."""
    payload = {
        "nome": "Sem Email",
        "password": "senha123",
        "administrador": "false",
    }
    resp = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp.status_code == 400
    assert "email" in resp.json()


@pytest.mark.usuarios
def test_cadastrar_usuario_sem_password():
    """Omitir o campo 'password' deve retornar 400."""
    payload = {
        "nome": "Sem Senha",
        "email": email_unico(),
        "administrador": "false",
    }
    resp = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp.status_code == 400
    assert "password" in resp.json()


# ─────────────────────────────────────────────
# GET /usuarios/{_id}
# ─────────────────────────────────────────────

@pytest.mark.usuarios
def test_buscar_usuario_por_id_valido(usuario_criado):
    """Buscar usuário por _id existente deve retornar 200 e schema correto."""
    usuario_id = usuario_criado["_id"]
    resp = requests.get(f"{BASE_URL}/usuarios/{usuario_id}")
    assert resp.status_code == 200
    jsonschema.validate(instance=resp.json(), schema=SCHEMA_USUARIO)


@pytest.mark.usuarios
def test_buscar_usuario_por_id_inexistente():
    """Buscar usuário com _id que não existe deve retornar 400."""
    resp = requests.get(f"{BASE_URL}/usuarios/id_que_nao_existe")
    assert resp.status_code == 400
    assert "Usuário não encontrado" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# PUT /usuarios/{_id}
# ─────────────────────────────────────────────

@pytest.mark.usuarios
def test_atualizar_usuario_valido(usuario_criado):
    """Atualizar usuário existente com dados válidos deve retornar 200."""
    usuario_id = usuario_criado["_id"]
    payload = {
        "nome": "Nome Atualizado",
        "email": email_unico(),
        "password": "novaSenha456",
        "administrador": "false",
    }
    resp = requests.put(f"{BASE_URL}/usuarios/{usuario_id}", json=payload)
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.usuarios
def test_atualizar_usuario_id_inexistente():
    """Atualizar usuário com _id inexistente deve criar um novo (201)."""
    payload = {
        "nome": "Novo Via PUT",
        "email": email_unico(),
        "password": "senha789",
        "administrador": "false",
    }
    resp = requests.put(f"{BASE_URL}/usuarios/id_inexistente_xyz", json=payload)
    assert resp.status_code in (200, 201)
    if resp.status_code == 201:
        novo_id = resp.json().get("_id")
        if novo_id:
            requests.delete(f"{BASE_URL}/usuarios/{novo_id}")


# ─────────────────────────────────────────────
# DELETE /usuarios/{_id}
# ─────────────────────────────────────────────

@pytest.mark.usuarios
def test_excluir_usuario_existente():
    """Excluir usuário existente deve retornar 200 com mensagem de sucesso."""
    payload = {
        "nome": "Para Deletar",
        "email": email_unico(),
        "password": "senha123",
        "administrador": "false",
    }
    resp_create = requests.post(f"{BASE_URL}/usuarios", json=payload)
    assert resp_create.status_code == 201
    usuario_id = resp_create.json()["_id"]

    resp_del = requests.delete(f"{BASE_URL}/usuarios/{usuario_id}")
    assert resp_del.status_code == 200
    assert "Registro excluído com sucesso" in resp_del.json().get("message", "")


@pytest.mark.usuarios
def test_excluir_usuario_inexistente():
    """Excluir usuário com _id inexistente deve retornar 200 com aviso."""
    resp = requests.delete(f"{BASE_URL}/usuarios/id_nao_existe_999")
    assert resp.status_code == 200
    assert "Nenhum registro excluído" in resp.json().get("message", "")
