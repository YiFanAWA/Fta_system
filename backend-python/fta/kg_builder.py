import re

from neo4j import GraphDatabase
from core.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from core.utils import log

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


_TEXT_TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")
_SYMBOL_RE = re.compile(r"[^A-Za-z0-9\u4e00-\u9fff\s]")
_NOISE_START_RE = re.compile(r"^[\s:：,，;；\-\._]+")
_NOISE_SNIPPET_RE = re.compile(r'^(?:%\d+|bin["\'”’)]?)$', re.IGNORECASE)


def _semantic_key(text):
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[，。；：、,.!?:;\-_/()（）\[\]{}\"'`]+", "", s)
    return s


def _has_unbalanced_brackets(text):
    pairs = [("(", ")"), ("（", "）"), ("[", "]"), ("{", "}")]
    for left, right in pairs:
        left_count = text.count(left)
        right_count = text.count(right)
        if left_count != right_count:
            return True
    return False


def _is_valid_event_name(text):
    name = (text or "").strip()
    if not name:
        return False

    if _NOISE_START_RE.match(name):
        return False

    if _NOISE_SNIPPET_RE.match(name):
        return False

    if len(_TEXT_TOKEN_RE.findall(name)) == 0:
        return False

    if _has_unbalanced_brackets(name):
        return False

    symbol_count = len(_SYMBOL_RE.findall(name))
    if symbol_count > 0 and symbol_count / max(len(name), 1) > 0.35:
        return False

    return True


def _normalize_failure_items(failures):
    normalized = []
    seen = set()

    for item in failures:
        if isinstance(item, str):
            name = item.strip()
            key = _semantic_key(name)
            if not _is_valid_event_name(name) or not key or key in seen:
                continue
            seen.add(key)
            normalized.append({
                "name": name,
                "probability": None,
                "gate": "OR",
                "causes": []
            })
            continue

        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        clean_name = name.strip()
        name_key = _semantic_key(clean_name)
        if not _is_valid_event_name(clean_name) or not name_key or name_key in seen:
            continue
        seen.add(name_key)

        causes = item.get("causes", [])
        if not isinstance(causes, list):
            causes = []

        normalized_causes = []
        cause_seen = set()
        for cause in causes:
            if isinstance(cause, str):
                cause_name = cause.strip()
                cause_prob = None
            elif isinstance(cause, dict):
                raw_name = cause.get("name")
                cause_name = raw_name.strip() if isinstance(raw_name, str) else ""
                cause_prob = cause.get("probability")
            else:
                continue

            cause_key = _semantic_key(cause_name)
            if not _is_valid_event_name(cause_name) or not cause_key or cause_key in cause_seen:
                continue

            cause_seen.add(cause_key)
            normalized_causes.append({
                "name": cause_name,
                "probability": cause_prob
            })

        normalized.append({
            "name": clean_name,
            "probability": item.get("probability"),
            "gate": item.get("gate", "OR"),
            "causes": normalized_causes
        })

    return normalized


def create_failure_nodes(system, failures):
    if not isinstance(system, str) or not system.strip():
        raise ValueError("system不能为空")

    if not isinstance(failures, list):
        raise ValueError("failures必须是列表")

    normalized = _normalize_failure_items(failures)
    if not normalized:
        raise ValueError("failures中没有有效故障数据")

    try:
        with driver.session() as session:

            for item in normalized:
                query = """
                MERGE (s:System {name:$system})
                MERGE (f:Failure {name:$failure})
                SET f.probability = coalesce($probability, f.probability),
                    f.gate = coalesce($gate, f.gate, 'OR')
                MERGE (f)-[:LEADS_TO]->(s)
                """

                session.run(
                    query,
                    system=system.strip(),
                    failure=item["name"],
                    probability=item["probability"],
                    gate=item.get("gate", "OR")
                )

                for cause in item.get("causes", []):
                    cause_query = """
                    MERGE (c:Failure {name:$cause})
                    SET c.probability = coalesce($probability, c.probability)
                    MERGE (f:Failure {name:$failure})
                    MERGE (c)-[:CAUSES]->(f)
                    """
                    session.run(
                        cause_query,
                        cause=cause["name"],
                        probability=cause.get("probability"),
                        failure=item["name"]
                    )
    except Exception as exc:
        log(f"写入Neo4j失败: {exc}")
        raise RuntimeError("写入知识图谱失败") from exc