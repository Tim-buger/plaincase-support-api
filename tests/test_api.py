def test_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extracts_a_structured_ticket(client):
    response = client.post(
        "/api/v1/extract/support-ticket",
        headers={"Idempotency-Key": "checkout-outage-001"},
        json={
            "provider": "mock",
            "text": "Our production API is down and checkout is blocked. This is urgent.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["category"] == "technical"
    assert payload["data"]["priority"] == "urgent"
    assert payload["data"]["requires_human"] is True
    assert payload["meta"]["validated"] is True
    assert payload["meta"]["cached"] is False


def test_idempotency_reuses_completed_result(client):
    headers = {"Idempotency-Key": "duplicate-safe-001"}
    body = {"provider": "mock", "text": "I was charged twice and need a refund today."}

    first = client.post("/api/v1/extract/support-ticket", headers=headers, json=body)
    second = client.post("/api/v1/extract/support-ticket", headers=headers, json=body)

    assert first.status_code == second.status_code == 200
    assert first.json()["meta"]["request_id"] == second.json()["meta"]["request_id"]
    assert second.json()["meta"]["cached"] is True


def test_rejects_short_input(client):
    response = client.post(
        "/api/v1/extract/support-ticket",
        json={"provider": "mock", "text": "short"},
    )

    assert response.status_code == 422


def test_audit_history(client):
    client.post(
        "/api/v1/extract/support-ticket",
        json={"provider": "mock", "text": "I cannot log in to my customer account."},
    )

    response = client.get("/api/v1/audit/recent")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "ok"

