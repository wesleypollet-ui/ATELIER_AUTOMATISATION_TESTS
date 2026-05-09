import json
from flask import Flask, render_template, jsonify, Response
from runner import run as run_tests
import storage

app = Flask(__name__)
storage.init_db()


@app.get("/")
def home():
    return render_template("consignes.html")


@app.get("/run")
def run_endpoint():
    """Déclenche un run de tests, sauvegarde en SQLite, retourne le JSON."""
    try:
        result = run_tests()
        storage.save_run(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "details": str(e),
        }), 500


@app.get("/dashboard")
def dashboard():
    """Affiche l'historique des runs + détail du dernier run."""
    runs = storage.list_runs(limit=20)
    last = runs[0] if runs else None
    return render_template("dashboard.html", runs=runs, last=last)


@app.get("/health")
def health():
    """Retourne l'état de santé de la solution basé sur le dernier run."""
    last = storage.get_last_run()

    if last is None:
        return jsonify({
            "status": "unknown",
            "last_run": None
        }), 200

    summary = last["summary"]

    if summary["error_rate"] == 0:
        status = "ok"
    elif summary["error_rate"] < 0.5:
        status = "degraded"
    else:
        status = "critical"

    return jsonify({
        "status": status,
        "last_run": last["timestamp"],
        "error_rate": summary["error_rate"],
        "availability_pct": summary["availability_pct"],
        "latency_ms_avg": summary["latency_ms_avg"],
        "latency_ms_p95": summary["latency_ms_p95"],
    }), 200


@app.get("/export")
def export():
    """Export JSON téléchargeable des 20 derniers runs."""
    runs = storage.list_runs(limit=20)
    return Response(
        json.dumps(runs, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=runs_export.json"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
