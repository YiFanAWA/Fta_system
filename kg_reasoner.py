from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from utils import log

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


def get_failure_paths(system):
    if not isinstance(system, str) or not system.strip():
        raise ValueError("system不能为空")

    query = """
    MATCH (f:Failure)-[:LEADS_TO]->(s:System {name:$system})
    OPTIONAL MATCH (c:Failure)-[:CAUSES]->(f)
    RETURN f.name AS failure,
           f.probability AS failure_probability,
           coalesce(f.gate, 'OR') AS gate,
           collect(DISTINCT {
               name: c.name,
               probability: c.probability
           }) AS causes
    ORDER BY failure
    """

    try:
        with driver.session() as session:

            result = session.run(query, system=system.strip())

            failures = []
            for r in result:
                name = r.get("failure")
                if not name:
                    continue

                causes_raw = r.get("causes") or []
                causes = []
                for cause in causes_raw:
                    cause_name = cause.get("name") if isinstance(cause, dict) else None
                    if not cause_name:
                        continue
                    causes.append({
                        "name": cause_name,
                        "probability": cause.get("probability") if isinstance(cause, dict) else None
                    })

                failures.append({
                    "name": name,
                    "probability": r.get("failure_probability"),
                    "gate": r.get("gate") or "OR",
                    "causes": causes
                })
    except Exception as exc:
        log(f"读取Neo4j失败: {exc}")
        raise RuntimeError("知识图谱推理失败") from exc

    return failures


def query_knowledge_graph(cypher, params=None, limit=200):
    if not isinstance(cypher, str) or not cypher.strip():
        raise ValueError("cypher不能为空")

    query_text = cypher.strip()
    lowered = query_text.lower()
    forbidden = [" delete ", " detach ", " remove ", " drop ", " create ", " merge ", " set "]
    if any(token in f" {lowered} " for token in forbidden):
        raise ValueError("/api/kg/query仅允许只读查询")

    safe_params = params if isinstance(params, dict) else {}
    if not isinstance(limit, int) or limit <= 0:
        limit = 200
    limit = min(limit, 1000)

    wrapped = f"CALL () {{ {query_text} }} RETURN * LIMIT $api_limit"

    try:
        with driver.session() as session:
            result = session.run(wrapped, **safe_params, api_limit=limit)
            rows = [record.data() for record in result]
    except Exception as exc:
        log(f"执行Cypher失败: {exc}")
        raise RuntimeError("知识图谱查询失败") from exc

    return {
        "count": len(rows),
        "rows": rows,
    }