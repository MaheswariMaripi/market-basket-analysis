"""Tests for the Flask web application API."""

import pytest

from app.app import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Market Basket Analysis" in response.data
    assert b"Rule Explorer" in response.data


def test_api_products(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.get_json()["products"]
    assert isinstance(products, list)
    assert products == sorted(products)
    assert len(products) > 0


def test_api_recommend_empty_basket(client):
    response = client.post("/api/recommend", json={"products": []})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_recommend_known_basket(client):
    products = client.get("/api/products").get_json()["products"]
    response = client.post("/api/recommend", json={"products": products[:2]})
    assert response.status_code == 200
    body = response.get_json()
    if "recommendations" in body:
        for rec in body["recommendations"]:
            assert {"product", "confidence", "lift", "rule"} <= set(rec)


def test_api_rules_filter_and_pagination(client):
    response = client.get("/api/rules?product=milk&min_lift=1.5&limit=10")
    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] <= 10
    assert all(r["lift"] >= 1.5 for r in body["rules"])
    for rule in body["rules"]:
        joined = " ".join(rule["antecedents"] + rule["consequents"]).lower()
        assert "milk" in joined


def test_api_rules_rejects_oversized_limit(client):
    response = client.get("/api/rules?limit=99999")
    body = response.get_json()
    assert body["count"] <= 500


def test_api_top_rules(client):
    response = client.get("/api/top_rules")
    assert response.status_code == 200
    combos = response.get_json()["top_combinations"]
    assert len(combos) == 10
    lifts = [c["lift"] for c in combos]
    assert lifts == sorted(lifts, reverse=True)
