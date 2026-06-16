import uuid
import pytest
import requests

BASE_URL = "https://compassuol.serverest.dev"


def email_unico():
    """Gera um e-mail único para evitar conflitos entre testes."""
    return f"qa_{uuid.uuid4().hex[:8]}@teste.com"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def usuario_payload():
    """Payload válido para criação de usuário comum."""
    return {
        "nome": "QA Tester",
        "email": email_unico(),
        "password": "senha123",
        "administrador": "false",
    }


@pytest.fixture
def admin_payload():
    """Payload válido para criação de usuário administrador."""
    return {
        "nome": "Admin QA",
        "email": email_unico(),
        "password": "senha123",
        "administrador": "true",
    }


@pytest.fixture
def usuario_criado(base_url, usuario_payload):
    """Cria um usuário comum e retorna seus dados. Remove ao final do teste."""
    resp = requests.post(f"{base_url}/usuarios", json=usuario_payload)
    assert resp.status_code == 201, f"Falha ao criar usuário de teste: {resp.text}"
    usuario_id = resp.json()["_id"]
    yield {**usuario_payload, "_id": usuario_id}
    requests.delete(f"{base_url}/usuarios/{usuario_id}")


@pytest.fixture
def admin_criado(base_url, admin_payload):
    """Cria um usuário administrador e retorna seus dados. Remove ao final do teste."""
    resp = requests.post(f"{base_url}/usuarios", json=admin_payload)
    assert resp.status_code == 201, f"Falha ao criar admin de teste: {resp.text}"
    usuario_id = resp.json()["_id"]
    yield {**admin_payload, "_id": usuario_id}
    requests.delete(f"{base_url}/usuarios/{usuario_id}")


@pytest.fixture
def token_admin(base_url, admin_criado):
    """Realiza login com admin e retorna o Bearer token."""
    resp = requests.post(
        f"{base_url}/login",
        json={"email": admin_criado["email"], "password": admin_criado["password"]},
    )
    assert resp.status_code == 200, f"Falha ao obter token admin: {resp.text}"
    return resp.json()["authorization"]


@pytest.fixture
def headers_admin(token_admin):
    """Header de autorização pronto para uso."""
    return {"Authorization": token_admin}
