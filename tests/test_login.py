"""
Testes do endpoint /login da API ServeRest.
Parte 2: fluxos de autenticação — credenciais válidas, inválidas e campos ausentes.
"""
import pytest
import requests

BASE_URL = "https://compassuol.serverest.dev"


# ─────────────────────────────────────────────
# POST /login — credenciais corretas
# ─────────────────────────────────────────────

@pytest.mark.login
def test_login_credenciais_validas(admin_criado):
    """Login com credenciais corretas deve retornar 200 e um token Bearer."""
    payload = {"email": admin_criado["email"], "password": admin_criado["password"]}
    resp = requests.post(f"{BASE_URL}/login", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    assert "authorization" in body
    assert body["authorization"].startswith("Bearer ")
    assert body["message"] == "Login realizado com sucesso"


@pytest.mark.login
def test_login_retorna_token_nao_vazio(admin_criado):
    """O token retornado no login não deve ser uma string vazia."""
    payload = {"email": admin_criado["email"], "password": admin_criado["password"]}
    resp = requests.post(f"{BASE_URL}/login", json=payload)
    token = resp.json().get("authorization", "")
    assert len(token) > 0


# ─────────────────────────────────────────────
# POST /login — senha errada
# ─────────────────────────────────────────────

@pytest.mark.login
def test_login_senha_errada(admin_criado):
    """Login com senha incorreta deve retornar 401."""
    payload = {"email": admin_criado["email"], "password": "senha_errada_999"}
    resp = requests.post(f"{BASE_URL}/login", json=payload)
    assert resp.status_code == 401
    assert "Email e/ou senha inválidos" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# POST /login — e-mail inexistente
# ─────────────────────────────────────────────

@pytest.mark.login
def test_login_email_inexistente():
    """Login com e-mail que não existe no sistema deve retornar 401."""
    payload = {
        "email": "usuario_que_nao_existe@fantasma.com",
        "password": "qualquerSenha",
    }
    resp = requests.post(f"{BASE_URL}/login", json=payload)
    assert resp.status_code == 401
    assert "Email e/ou senha inválidos" in resp.json().get("message", "")


# ─────────────────────────────────────────────
# POST /login — campos ausentes
# ─────────────────────────────────────────────

@pytest.mark.login
def test_login_sem_email():
    """Omitir e-mail no login deve retornar 400."""
    resp = requests.post(f"{BASE_URL}/login", json={"password": "senha123"})
    assert resp.status_code == 400
    assert "email" in resp.json()


@pytest.mark.login
def test_login_sem_password():
    """Omitir senha no login deve retornar 400."""
    resp = requests.post(f"{BASE_URL}/login", json={"email": "alguem@teste.com"})
    assert resp.status_code == 400
    assert "password" in resp.json()


@pytest.mark.login
def test_login_body_vazio():
    """Enviar body vazio no login deve retornar 400."""
    resp = requests.post(f"{BASE_URL}/login", json={})
    assert resp.status_code == 400
