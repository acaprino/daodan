"""Zero perdite dello stack dal fork rispetto al registro di `develop` 68b784e (T0.A.3).

Una perdita è un nome di `score.frameworks_by_name.missed` o `score.services.missed` di `results/daodan_stack.json` che
non è in `score.before.<stessa misura>.missed` di `results/daodan_stack_fork_develop_68b784e.json`, per ogni fixture
presente in tutti e due. Ogni perdita ammessa sta in ACCEPTED con fixture, misura, nome e motivo, accettata dal
proprietario; oggi non ce n'è nessuna.
"""
import json
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
MEASURES = ("frameworks_by_name", "services")
# (fixture, misura, nome): motivo accettato dal proprietario
MOTIVO_A = "Lo stack senza le dichiarazioni della pre-mappa (T1.B.7), accettato dal proprietario il 27 novembre 2026 fino al rilascio .6 del fork (benchmarks/stack-build-tools/README.md)"
MOTIVO_B = "Fuori dalle 88 di T1.B.1: viene da .github/ o da una dichiarazione che lo stack non vede più; accettato dal proprietario il 27 novembre 2026 finché il perimetro non legge .github/"
ACCEPTED: dict[tuple[str, str, str], str] = {
    ("jvm-gradle-computed-deps", "frameworks_by_name", "jackson"): MOTIVO_A,
    ("jvm-sbt-two-subprojects", "frameworks_by_name", "cats"): MOTIVO_A,
    ("jvm-sbt-two-subprojects", "frameworks_by_name", "scalatest"): MOTIVO_A,
    ("mix-real-klaxon", "frameworks_by_name", "testng"): MOTIVO_A,
    ("real-app-jhipster-sample", "services", "postgresql"): MOTIVO_A,
    ("real-app-jhipster-sample", "services", "h2"): MOTIVO_A,
    ("real-app-kotlinconf", "services", "githubpages"): MOTIVO_B,
    ("real-stack-bakerydemo", "frameworks_by_name", "django"): MOTIVO_A,
    ("real-stack-bakerydemo", "frameworks_by_name", "wagtail"): MOTIVO_A,
    ("real-stack-bakerydemo", "services", "elasticsearch"): MOTIVO_A,
    ("real-stack-documenso", "services", "gotenberg"): MOTIVO_A,
    ("real-stack-docuseal", "services", "redis"): MOTIVO_A,
    ("real-stack-peopleinspace", "frameworks_by_name", "kotlintest"): MOTIVO_B,
    ("real-svc-eshop", "frameworks_by_name", "mstest"): MOTIVO_A,
    ("real-svc-otel-demo", "services", "prometheus"): MOTIVO_A,
}
# Aggiunte il 26 novembre 2026: non hanno un «prima».
WITHOUT_BEFORE = frozenset({"real-auth0-go", "real-bank-of-anthos", "real-microblog", "real-next-subscriptions",
                            "real-stack-polar", "real-sveltekit-realworld"})


def _fixtures(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))["fixtures"]


def losses() -> list[tuple[str, str, str]]:
    after = _fixtures("daodan_stack.json")
    before = _fixtures("daodan_stack_fork_develop_68b784e.json")
    found = []
    for fixture in sorted(set(after) & set(before)):
        now = after[fixture].get("score")
        old = (before[fixture].get("score") or {}).get("before")
        if not now or not old:  # la corsa è finita in errore: non ha misure
            continue
        for measure in MEASURES:
            known = set(old[measure]["missed"])
            found += [(fixture, measure, name) for name in now[measure]["missed"] if name not in known]
    return found


def test_no_loss_against_the_registry_before_the_fork():
    unaccepted = [loss for loss in losses() if loss not in ACCEPTED]
    assert not unaccepted, f"perdite non accettate: {unaccepted}"


def test_fixtures_without_a_before_are_the_ones_named():
    after = set(_fixtures("daodan_stack.json"))
    before = set(_fixtures("daodan_stack_fork_develop_68b784e.json"))
    assert after - before == WITHOUT_BEFORE
    assert not before - after
