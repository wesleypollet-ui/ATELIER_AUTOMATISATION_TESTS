import time
import requests

BASE_URL = "https://cataas.com"
TIMEOUT = 10
MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class ApiCallError(Exception):
    """Erreur levée quand l'API échoue après plusieurs tentatives."""


def call_api(
    path: str,
    method: str = "GET",
    params: dict | None = None,
    headers: dict | None = None,
    expected_status: int = 200,
) -> tuple[requests.Response, int]:
    """
    Appelle l'API avec timeout + retry simple.
    Retourne (response, latency_ms).

    - retry sur erreurs réseau
    - retry sur 429 et 5xx
    - backoff simple : 1s, 2s, 3s
    - lève une erreur claire si toutes les tentatives échouent
    """
    url = f"{BASE_URL}{path}"
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.perf_counter()

            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=TIMEOUT,
            )

            latency_ms = round((time.perf_counter() - start) * 1000)

            if response.status_code in RETRY_STATUS_CODES:
                last_error = ApiCallError(
                    f"Statut temporaire {response.status_code} sur {url}"
                )
                if attempt < MAX_RETRIES:
                    time.sleep(attempt)
                    continue
                raise last_error

            if response.status_code != expected_status:
                raise ApiCallError(
                    f"Statut inattendu pour {url} : "
                    f"attendu={expected_status}, obtenu={response.status_code}"
                )

            return response, latency_ms

        except requests.Timeout as exc:
            last_error = ApiCallError(f"Timeout sur {url}: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(attempt)
                continue

        except requests.RequestException as exc:
            last_error = ApiCallError(f"Erreur réseau sur {url}: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(attempt)
                continue

    raise last_error if last_error else ApiCallError(f"Échec appel API sur {url}")


def read_json(response: requests.Response) -> dict | list:
    """
    Parse le JSON de manière sécurisée.
    Lève ApiCallError si la réponse n'est pas un JSON valide.
    """
    try:
        return response.json()
    except ValueError as exc:
        raise ApiCallError("Réponse JSON invalide") from exc


def test_random_cat_returns_image():
    response, latency_ms = call_api("/cat")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")
    return {"latency_ms": latency_ms}


def test_cat_says_returns_image():
    response, latency_ms = call_api("/cat/says/Bonjour")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")
    return {"latency_ms": latency_ms}


def test_random_cat_json_format():
    response, latency_ms = call_api(
        "/cat",
        params={"json": "true"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")

    data = read_json(response)
    assert isinstance(data, dict)
    assert len(data) > 0

    return {"latency_ms": latency_ms}


def test_cat_json_has_id():
    response, latency_ms = call_api(
        "/cat",
        params={"json": "true"},
        headers={"Accept": "application/json"},
    )

    data = read_json(response)
    assert "_id" in data
    assert isinstance(data["_id"], str)

    return {"latency_ms": latency_ms}


def test_cat_json_has_tags():
    response, latency_ms = call_api(
        "/cat",
        params={"json": "true"},
        headers={"Accept": "application/json"},
    )

    data = read_json(response)
    assert "tags" in data
    assert isinstance(data["tags"], list)

    return {"latency_ms": latency_ms}


def test_tags_returns_json_array():
    response, latency_ms = call_api("/api/tags")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")

    data = read_json(response)
    assert isinstance(data, list)

    if len(data) > 0:
        assert isinstance(data[0], str)

    return {"latency_ms": latency_ms}


def test_cats_search_with_params():
    response, latency_ms = call_api(
        "/api/cats",
        params={"tags": "cute", "skip": 0, "limit": 5},
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")

    data = read_json(response)
    assert isinstance(data, list)

    return {"latency_ms": latency_ms}


def test_invalid_route_returns_404():
    response, latency_ms = call_api(
        "/route-inexistante-xyz",
        expected_status=404,
    )

    assert response.status_code == 404
    return {"latency_ms": latency_ms}


def test_cat_with_text_and_color():
    response, latency_ms = call_api(
        "/cat/says/Hello",
        params={"color": "red", "size": 50},
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")

    return {"latency_ms": latency_ms}


ALL_TESTS = [
    test_random_cat_returns_image,
    test_cat_says_returns_image,
    test_random_cat_json_format,
    test_cat_json_has_id,
    test_cat_json_has_tags,
    test_tags_returns_json_array,
    test_cats_search_with_params,
    test_invalid_route_returns_404,
    test_cat_with_text_and_color,
]
