"""Career Navigator & Skill Gap Agent (Neo4j)

pip install neo4j anthropic
env: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, (optional) ANTHROPIC_API_KEY
"""
import json
import os
import sys

from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
)

# ---------- Profile storage ----------
def save_profile(pid, name, skills, goal_role):
    """skills: dict {skill_name: level 1-5}"""
    with driver.session() as s:
        s.run("MERGE (p:Person {id:$pid}) SET p.name=$name", pid=pid, name=name)
        s.run("MATCH (p:Person {id:$pid})-[r:HAS_SKILL]->() DELETE r", pid=pid)
        for skill, level in skills.items():
            s.run(
                """MATCH (p:Person {id:$pid})
                   MERGE (k:Skill {name:$skill})
                   MERGE (p)-[:HAS_SKILL {level:$level}]->(k)""",
                pid=pid, skill=skill, level=level,
            )
        s.run("MATCH (p:Person {id:$pid})-[r:WANTS_ROLE]->() DELETE r", pid=pid)
        s.run(
            """MATCH (p:Person {id:$pid}), (r:JobRole {title:$role})
               MERGE (p)-[:WANTS_ROLE]->(r)""",
            pid=pid, role=goal_role,
        )

def mark_completed(pid, resource_title):
    with driver.session() as s:
        s.run(
            """MATCH (p:Person {id:$pid}), (l:LearningResource {title:$t})
               MERGE (p)-[:COMPLETED]->(l)
               WITH p, l MATCH (l)-[:TEACHES]->(k:Skill)
               MERGE (p)-[:HAS_SKILL]->(k)""",
            pid=pid, t=resource_title,
        )

# ---------- Skill gap analysis ----------
GAP_QUERY = """
MATCH (p:Person {id:$pid})-[:WANTS_ROLE]->(r:JobRole)-[req:REQUIRES]->(t:Skill)
// required skill + everything that must be learned before it
MATCH (s:Skill)-[:PREREQUISITE_OF*0..]->(t)
WHERE NOT (p)-[:HAS_SKILL]->(s)
WITH p, s, max(req.importance) AS importance
// how many missing prerequisites sit below this skill (0 = start here)
OPTIONAL MATCH (pre:Skill)-[:PREREQUISITE_OF*1..]->(s)
WHERE NOT (p)-[:HAS_SKILL]->(pre)
WITH p, s, importance, count(DISTINCT pre) AS missing_prereqs
OPTIONAL MATCH (res:LearningResource)-[:TEACHES]->(s)
WHERE NOT (p)-[:COMPLETED]->(res)
RETURN s.name AS skill, importance, missing_prereqs,
       collect(DISTINCT {title: res.title, url: res.url, hours: res.hours}) AS resources
ORDER BY missing_prereqs ASC, importance DESC
"""

MATCH_QUERY = """
MATCH (p:Person {id:$pid})-[:WANTS_ROLE]->(r:JobRole)-[:REQUIRES]->(s:Skill)
WITH r, count(s) AS total,
     sum(CASE WHEN EXISTS { MATCH (:Person {id:$pid})-[:HAS_SKILL]->(s) } THEN 1 ELSE 0 END) AS have
RETURN r.title AS role, have, total
"""

def analyze(pid):
    with driver.session() as s:
        gaps = [r.data() for r in s.run(GAP_QUERY, pid=pid)]
        match = s.run(MATCH_QUERY, pid=pid).single()
    return {"match": match.data() if match else None, "learning_path": gaps}

# ---------- Optional: LLM explanation ----------
def explain(result):
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    msg = anthropic.Anthropic().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": "Turn this graph-derived skill-gap analysis into a short, "
                       "encouraging learning plan. Keep the order given.\n\n"
                       + json.dumps(result, indent=2),
        }],
    )
    return msg.content[0].text

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "u1"
    result = analyze(pid)
    print(json.dumps(result, indent=2))
    text = explain(result)
    if text:
        print("\n--- Personalized plan ---\n" + text)
    driver.close()
