"""
Tests dels endpoints de l'API.
Comproven que les rutes bàsiques responguin correctament.
"""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(http_client):
    """GET /health ha de retornar 200."""
    response = await http_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_body(http_client):
    """GET /health ha de retornar status ok i version."""
    response = await http_client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "env" in data


@pytest.mark.asyncio
async def test_health_version_format(http_client):
    """La version ha de tenir format semver (X.Y.Z)."""
    response = await http_client.get("/health")
    version = response.json()["version"]
    parts = version.split(".")
    assert len(parts) == 3, f"Format de versió incorrecte: {version}"
    assert all(p.isdigit() for p in parts), f"Versió no numèrica: {version}"


@pytest.mark.asyncio
async def test_api_root_returns_200(http_client):
    """GET /api/v1 ha de retornar 200."""
    response = await http_client.get("/api/v1")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_root_has_version(http_client):
    """GET /api/v1 ha de retornar el camp version."""
    response = await http_client.get("/api/v1")
    data = response.json()
    assert "version" in data
    assert data["version"] == "v1"


@pytest.mark.asyncio
async def test_nonexistent_route_returns_404(http_client):
    """Una ruta inexistent ha de retornar 404."""
    response = await http_client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_404_error_format(http_client):
    """El 404 ha de tenir format JSON consistent."""
    response = await http_client.get("/api/v1/nonexistent-route")
    data = response.json()
    # El nostre error handler retorna {"error": "...", "path": "..."}
    assert "error" in data


@pytest.mark.asyncio
async def test_cors_headers_present(http_client):
    """Les respostes han d'incloure headers CORS."""
    response = await http_client.get(
        "/health",
        headers={"Origin": "http://localhost:8080"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_docs_endpoint_available(http_client):
    """La documentació Swagger ha d'estar disponible a /api/docs."""
    response = await http_client.get("/api/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema_available(http_client):
    """L'esquema OpenAPI ha d'estar disponible a /api/openapi.json."""
    response = await http_client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "WealthPilot API"
