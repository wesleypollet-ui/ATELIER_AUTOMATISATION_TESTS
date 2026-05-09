import datetime
import json

from test_cataas_api import ALL_TESTS, ApiCallError
from qos_measure import run_qos


def run() -> dict:
    results = []

    for test_fn in ALL_TESTS:
        try:
            payload = test_fn() or {}
            result = {
                "name": test_fn.__name__,
                "status": "PASS",
                "latency_ms": payload.get("latency_ms"),
                "details": None,
            }
        except AssertionError as e:
            result = {
                "name": test_fn.__name__,
                "status": "FAIL",
                "latency_ms": None,
                "details": str(e),
            }
        except ApiCallError as e:
            result = {
                "name": test_fn.__name__,
                "status": "FAIL",
                "latency_ms": None,
                "details": str(e),
            }
        except Exception as e:
            result = {
                "name": test_fn.__name__,
                "status": "FAIL",
                "latency_ms": None,
                "details": f"Erreur inattendue : {e}",
            }

        results.append(result)

    qos = run_qos()

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed

    return {
        "api": "Cataas",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(results),
            "error_rate": qos["error_rate"],
            "availability_pct": qos["availability_pct"],
            "latency_ms_avg": qos["latency_ms_avg"],
            "latency_ms_p95": qos["latency_ms_p95"],
            "latency_ms_min": qos["latency_ms_min"],
            "latency_ms_max": qos["latency_ms_max"],
        },
        "tests": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
