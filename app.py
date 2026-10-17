# # """Resume-powered Career Navigator (Streamlit + Neo4j + Ollama)

# # Run:  streamlit run app.py
# # Needs career_navigator.py in the same folder, seed.cypher already loaded,
# # and Ollama running with the model below pulled.
# # """
# # import json
# # import os

# # import fitz  # pymupdf
# # import ollama
# # import streamlit as st

# # import pandas as pd

# # from career_navigator import analyze, driver, mark_completed, save_profile

# # MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# # st.set_page_config(page_title="Career Navigator", page_icon="🧭", layout="wide")
# # st.title("🧭 Career Navigator")


# # # ---------- Graph helpers ----------
# # def graph_list(query, key):
# #     with driver.session() as s:
# #         return [r[key] for r in s.run(query)]


# # def known_skills():
# #     return graph_list("MATCH (s:Skill) RETURN s.name AS n ORDER BY n", "n")


# # def known_roles():
# #     return graph_list("MATCH (r:JobRole) RETURN r.title AS n ORDER BY n", "n")


# # def owned_skills(pid="me"):
# #     with driver.session() as s:
# #         return [r["n"] for r in s.run(
# #             "MATCH (:Person {id:$pid})-[:HAS_SKILL]->(s:Skill) RETURN s.name AS n", pid=pid)]


# # def role_scores(pid="me"):
# #     """Importance-weighted fit (%) for every role in the graph."""
# #     q = """
# #     MATCH (r:JobRole)-[req:REQUIRES]->(s:Skill)
# #     OPTIONAL MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(s)
# #     WITH r, sum(req.importance) AS total,
# #          sum(CASE WHEN p IS NULL THEN 0 ELSE req.importance END) AS have
# #     RETURN r.title AS role, round(100.0 * have / total) AS pct
# #     ORDER BY pct DESC
# #     """
# #     with driver.session() as s:
# #         return [r.data() for r in s.run(q, pid=pid)]


# # def path_dot(path):
# #     """Graphviz picture: green = you have it, orange = gap; arrows = prerequisite."""
# #     gaps = [g["skill"] for g in path]
# #     owned = set(owned_skills())
# #     with driver.session() as s:
# #         edges = [(r["a"], r["b"]) for r in s.run(
# #             "MATCH (a:Skill)-[:PREREQUISITE_OF]->(b:Skill) WHERE b.name IN $g "
# #             "RETURN a.name AS a, b.name AS b", g=gaps)]
# #     nodes = set(gaps) | {a for a, _ in edges}
# #     lines = ['digraph G { rankdir=LR; node [shape=box, style=filled, fontname=Helvetica];']
# #     for n in nodes:
# #         color = "#9be7a8" if n in owned else "#ffd29b"
# #         lines.append(f'"{n}" [fillcolor="{color}"];')
# #     for a, b in edges:
# #         lines.append(f'"{a}" -> "{b}";')
# #     lines.append("}")
# #     return "\n".join(lines)


# # # ---------- Resume extraction ----------
# # def pdf_to_text(file):
# #     doc = fitz.open(stream=file.read(), filetype="pdf")
# #     return "\n".join(page.get_text() for page in doc)


# # def extract_profile(text, skills):
# #     """LLM picks only skills from our canonical list -> built-in normalization."""
# #     prompt = (
# #         "Read this resume. Return JSON: "
# #         '{"name": "<full name>", "skills": ["<skill>", ...]}. '
# #         "Only include skills from this allowed list that the resume clearly shows:\n"
# #         f"{json.dumps(skills)}\n\nRESUME:\n{text[:6000]}"
# #     )
# #     out = ollama.chat(
# #         model=MODEL, format="json", messages=[{"role": "user", "content": prompt}]
# #     )["message"]["content"]
# #     data = json.loads(out)
# #     found = [s for s in data.get("skills", []) if s in skills]  # drop hallucinations
# #     return data.get("name", "Learner"), sorted(set(found))


# # # ---------- Career-only chatbot ----------
# # SYSTEM = (
# #     "You are a career guidance assistant. Answer ONLY career-related questions "
# #     "(skills, jobs, resumes, interviews, learning paths). Use ONLY the CONTEXT "
# #     "below for skills, courses and links; never invent any. If the context does "
# #     "not contain the answer, say so. Be concise and encouraging.\n\nCONTEXT:\n"
# # )


# # def is_career_question(msg):
# #     out = ollama.chat(
# #         model=MODEL,
# #         messages=[{
# #             "role": "user",
# #             "content": "Is this message about careers, jobs, skills, resumes, "
# #                        "interviews, studying or learning for work? "
# #                        f"Answer only YES or NO.\n\nMessage: {msg}",
# #         }],
# #     )["message"]["content"]
# #     return out.strip().upper().startswith("YES")


# # def stream_answer(history, context):
# #     msgs = [{"role": "system", "content": SYSTEM + json.dumps(context)}] + history[-6:]
# #     for chunk in ollama.chat(model=MODEL, messages=msgs, stream=True):
# #         yield chunk["message"]["content"]


# # # ---------- Sidebar: profile creation ----------
# # with st.sidebar:
# #     st.header("1. Your profile")
# #     pdf = st.file_uploader("Upload resume (PDF)", type="pdf")
# #     role = st.selectbox("Target role", known_roles())
# #     if st.button("Analyze my resume", type="primary", disabled=pdf is None):
# #         with st.spinner("Reading resume and updating graph..."):
# #             name, skills = extract_profile(pdf_to_text(pdf), known_skills())
# #             save_profile("me", name, {s: 3 for s in skills}, role)
# #             st.session_state.result = analyze("me")
# #             st.session_state.name, st.session_state.skills = name, skills
# #             st.session_state.chat = []

# # # ---------- Main area ----------
# # if "result" not in st.session_state:
# #     st.info("Upload your resume and pick a target role in the sidebar to begin.")
# #     st.stop()

# # res = st.session_state.result
# # tab1, tab2, tab3 = st.tabs(["📊 Skill gap & path", "🎯 Role fit", "💬 Career chat"])

# # with tab1:
# #     st.subheader(f"Hi {st.session_state.name}")
# #     st.write("**Skills found in your resume:**", ", ".join(st.session_state.skills) or "none")
# #     m = res["match"]
# #     if m:
# #         pct = int(100 * m["have"] / m["total"])
# #         st.metric(f"Match for {m['role']}", f"{pct}%", f"{m['have']}/{m['total']} required skills")
# #         st.progress(pct / 100)

# #     path = res["learning_path"]
# #     total_h = sum(
# #         (g["resources"][0]["hours"] or 0)
# #         for g in path if g["resources"] and g["resources"][0]["title"]
# #     )
# #     hpw = st.slider("Hours you can study per week", 2, 30, 8)
# #     c1, c2 = st.columns(2)
# #     c1.metric("Total study time", f"{total_h} h")
# #     c2.metric("Estimated time to be job-ready", f"{-(-total_h // hpw)} weeks")

# #     st.markdown("**Skill map** (green = you have it, orange = gap, arrow = learn first)")
# #     st.graphviz_chart(path_dot(path))

# #     st.subheader("Your learning path (learn top to bottom)")
# #     plan = [f"# Learning plan for {st.session_state.name}", ""]
# #     for i, g in enumerate(path, 1):
# #         titles = ", ".join(r["title"] for r in g["resources"] if r["title"]) or "no resource yet"
# #         plan.append(f"{i}. {g['skill']}: {titles}")
# #         with st.expander(f"{i}. {g['skill']}  (importance {g['importance']})"):
# #             for j, r in enumerate(g["resources"]):
# #                 if r["title"]:
# #                     a, b = st.columns([4, 1])
# #                     a.markdown(f"[{r['title']}]({r['url']}) , ~{r['hours']}h")
# #                     if b.button("Done ✅", key=f"done_{i}_{j}"):
# #                         mark_completed("me", r["title"])
# #                         st.session_state.result = analyze("me")
# #                         st.rerun()
# #     st.download_button("⬇️ Download my plan", "\n".join(plan), "learning_plan.md")

# # with tab2:
# #     st.subheader("How well you fit each role")
# #     scores = role_scores("me")
# #     st.bar_chart(pd.DataFrame(scores).set_index("role")["pct"])
# #     st.success(f"Best current fit: {scores[0]['role']} ({int(scores[0]['pct'])}%)")

# # with tab3:
# #     for m_ in st.session_state.chat:
# #         st.chat_message(m_["role"]).write(m_["content"])
# #     q = st.chat_input("Ask about your career path...")
# #     if q:
# #         st.session_state.chat.append({"role": "user", "content": q})
# #         st.chat_message("user").write(q)
# #         with st.chat_message("assistant"):
# #             if is_career_question(q):
# #                 ctx = {**res, "role_fit_percent": role_scores("me")}
# #                 ans = st.write_stream(stream_answer(st.session_state.chat, ctx))
# #             else:
# #                 ans = "I can only help with career-related questions, like skills, roles, resumes and learning paths."
# #                 st.write(ans)
# #         st.session_state.chat.append({"role": "assistant", "content": ans})



# """Resume-powered Career Navigator (Streamlit + Neo4j + Ollama)

# Run:  streamlit run app.py
# Needs career_navigator.py in the same folder, seed.cypher already loaded,
# and Ollama running with the model below pulled.
# """
# import json
# import os

# import fitz  # pymupdf
# import ollama
# import streamlit as st

# import pandas as pd

# from career_navigator import analyze, driver, mark_completed, save_profile

# MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# st.set_page_config(page_title="Career Navigator", page_icon="🧭", layout="wide")
# st.title("🧭 Career Navigator")


# # ---------- Graph helpers ----------
# def graph_list(query, key):
#     with driver.session() as s:
#         return [r[key] for r in s.run(query)]


# def known_skills():
#     return graph_list("MATCH (s:Skill) RETURN s.name AS n ORDER BY n", "n")


# def known_roles():
#     return graph_list("MATCH (r:JobRole) RETURN r.title AS n ORDER BY n", "n")


# def owned_skills(pid="me"):
#     with driver.session() as s:
#         return [r["n"] for r in s.run(
#             "MATCH (:Person {id:$pid})-[:HAS_SKILL]->(s:Skill) RETURN s.name AS n", pid=pid)]


# def role_scores(pid="me"):
#     """Importance-weighted fit (%) for every role in the graph."""
#     q = """
#     MATCH (r:JobRole)-[req:REQUIRES]->(s:Skill)
#     OPTIONAL MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(s)
#     WITH r, sum(req.importance) AS total,
#          sum(CASE WHEN p IS NULL THEN 0 ELSE req.importance END) AS have
#     RETURN r.title AS role, round(100.0 * have / total) AS pct
#     ORDER BY pct DESC
#     """
#     with driver.session() as s:
#         return [r.data() for r in s.run(q, pid=pid)]


# def path_dot(path):
#     """Graphviz picture: green = you have it, orange = gap; arrows = prerequisite."""
#     gaps = [g["skill"] for g in path]
#     owned = set(owned_skills())
#     with driver.session() as s:
#         edges = [(r["a"], r["b"]) for r in s.run(
#             "MATCH (a:Skill)-[:PREREQUISITE_OF]->(b:Skill) WHERE b.name IN $g "
#             "RETURN a.name AS a, b.name AS b", g=gaps)]
#     nodes = set(gaps) | {a for a, _ in edges}
#     lines = ['digraph G { rankdir=LR; node [shape=box, style=filled, fontname=Helvetica];']
#     for n in nodes:
#         color = "#9be7a8" if n in owned else "#ffd29b"
#         lines.append(f'"{n}" [fillcolor="{color}"];')
#     for a, b in edges:
#         lines.append(f'"{a}" -> "{b}";')
#     lines.append("}")
#     return "\n".join(lines)


# # ---------- Resume extraction ----------
# def pdf_to_text(file):
#     doc = fitz.open(stream=file.read(), filetype="pdf")
#     return "\n".join(page.get_text() for page in doc)


# def extract_profile(text, skills):
#     """LLM picks only skills from our canonical list -> built-in normalization."""
#     prompt = (
#         "Read this resume. Return JSON: "
#         '{"name": "<full name>", "skills": ["<skill>", ...]}. '
#         "Only include skills from this allowed list that the resume clearly shows:\n"
#         f"{json.dumps(skills)}\n\nRESUME:\n{text[:6000]}"
#     )
#     import re

#     # 1) Keyword matching (instant, works even if the model is not ready)
#     aliases = {
#         "Cloud (AWS)": ["aws", "amazon web services"],
#         "CI/CD": ["ci/cd", "github actions", "jenkins"],
#         "Machine Learning": ["machine learning", "scikit-learn", "sklearn"],
#         "Deep Learning": ["deep learning", "pytorch", "tensorflow", "keras"],
#         "NLP": ["nlp", "natural language"],
#         "HTML/CSS": ["html", "css"],
#         "Node.js": ["node.js", "nodejs", "express.js"],
#         "JavaScript": ["javascript", "js"],
#         "Data Visualization": ["data visualization", "matplotlib", "seaborn", "tableau"],
#         "Cybersecurity": ["cybersecurity", "cyber security", "pentest"],
#         "Data Structures": ["data structures", "dsa"],
#         "Kubernetes": ["kubernetes", "k8s"],
#         "APIs": ["api", "apis", "rest"],
#     }
#     low = text.lower()
#     found = set()
#     for sk in skills:
#         for term in aliases.get(sk, []) + [sk.lower()]:
#             if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", low):
#                 found.add(sk)
#                 break
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
#     name = lines[0][:40] if lines else "Learner"

#     # 2) LLM adds anything the keywords missed (skipped if Ollama is unavailable)
#     try:
#         out = ollama.chat(
#             model=MODEL, format="json", messages=[{"role": "user", "content": prompt}]
#         )["message"]["content"]
#         data = json.loads(out)
#         found |= {s for s in data.get("skills", []) if s in skills}  # drop hallucinations
#         name = data.get("name") or name
#     except Exception as e:
#         st.warning(f"AI model not available, used keyword matching instead ({type(e).__name__}).")
#     return name, sorted(found)


# # ---------- Career-only chatbot ----------
# SYSTEM = (
#     "You are a career guidance assistant. Answer ONLY career-related questions "
#     "(skills, jobs, resumes, interviews, learning paths). Use ONLY the CONTEXT "
#     "below for skills, courses and links; never invent any. If the context does "
#     "not contain the answer, say so. Be concise and encouraging.\n\nCONTEXT:\n"
# )


# def is_career_question(msg):
#     out = ollama.chat(
#         model=MODEL,
#         messages=[{
#             "role": "user",
#             "content": "Is this message about careers, jobs, skills, resumes, "
#                        "interviews, studying or learning for work? "
#                        f"Answer only YES or NO.\n\nMessage: {msg}",
#         }],
#     )["message"]["content"]
#     return out.strip().upper().startswith("YES")


# def stream_answer(history, context):
#     msgs = [{"role": "system", "content": SYSTEM + json.dumps(context)}] + history[-6:]
#     for chunk in ollama.chat(model=MODEL, messages=msgs, stream=True):
#         yield chunk["message"]["content"]


# # ---------- Sidebar: profile creation ----------
# with st.sidebar:
#     st.header("1. Your profile")
#     pdf = st.file_uploader("Upload resume (PDF)", type="pdf")
#     role = st.selectbox("Target role", known_roles())
#     if st.button("Analyze my resume", type="primary", disabled=pdf is None):
#         with st.spinner("Reading resume and updating graph..."):
#             name, skills = extract_profile(pdf_to_text(pdf), known_skills())
#             save_profile("me", name, {s: 3 for s in skills}, role)
#             st.session_state.result = analyze("me")
#             st.session_state.name, st.session_state.skills = name, skills
#             st.session_state.chat = []

# # ---------- Main area ----------
# if "result" not in st.session_state:
#     st.info("Upload your resume and pick a target role in the sidebar to begin.")
#     st.stop()

# res = st.session_state.result
# tab1, tab2, tab3 = st.tabs(["📊 Skill gap & path", "🎯 Role fit", "💬 Career chat"])

# with tab1:
#     st.subheader(f"Hi {st.session_state.name}")
#     st.write("**Skills found in your resume:**", ", ".join(st.session_state.skills) or "none")
#     m = res["match"]
#     if m:
#         pct = int(100 * m["have"] / m["total"])
#         st.metric(f"Match for {m['role']}", f"{pct}%", f"{m['have']}/{m['total']} required skills")
#         st.progress(pct / 100)

#     path = res["learning_path"]
#     total_h = sum(
#         (g["resources"][0]["hours"] or 0)
#         for g in path if g["resources"] and g["resources"][0]["title"]
#     )
#     hpw = st.slider("Hours you can study per week", 2, 30, 8)
#     c1, c2 = st.columns(2)
#     c1.metric("Total study time", f"{total_h} h")
#     c2.metric("Estimated time to be job-ready", f"{-(-total_h // hpw)} weeks")

#     st.markdown("**Skill map** (green = you have it, orange = gap, arrow = learn first)")
#     st.graphviz_chart(path_dot(path))

#     st.subheader("Your learning path (learn top to bottom)")
#     plan = [f"# Learning plan for {st.session_state.name}", ""]
#     for i, g in enumerate(path, 1):
#         titles = ", ".join(r["title"] for r in g["resources"] if r["title"]) or "no resource yet"
#         plan.append(f"{i}. {g['skill']}: {titles}")
#         with st.expander(f"{i}. {g['skill']}  (importance {g['importance']})"):
#             for j, r in enumerate(g["resources"]):
#                 if r["title"]:
#                     a, b = st.columns([4, 1])
#                     a.markdown(f"[{r['title']}]({r['url']}) , ~{r['hours']}h")
#                     if b.button("Done ✅", key=f"done_{i}_{j}"):
#                         mark_completed("me", r["title"])
#                         st.session_state.result = analyze("me")
#                         st.rerun()
#     st.download_button("⬇️ Download my plan", "\n".join(plan), "learning_plan.md")

# with tab2:
#     st.subheader("How well you fit each role")
#     scores = role_scores("me")
#     st.bar_chart(pd.DataFrame(scores).set_index("role")["pct"])
#     st.success(f"Best current fit: {scores[0]['role']} ({int(scores[0]['pct'])}%)")

# with tab3:
#     for m_ in st.session_state.chat:
#         st.chat_message(m_["role"]).write(m_["content"])
#     q = st.chat_input("Ask about your career path...")
#     if q:
#         st.session_state.chat.append({"role": "user", "content": q})
#         st.chat_message("user").write(q)
#         with st.chat_message("assistant"):
#             if is_career_question(q):
#                 ctx = {**res, "role_fit_percent": role_scores("me")}
#                 ans = st.write_stream(stream_answer(st.session_state.chat, ctx))
#             else:
#                 ans = "I can only help with career-related questions, like skills, roles, resumes and learning paths."
#                 st.write(ans)
#         st.session_state.chat.append({"role": "assistant", "content": ans})

"""Resume-powered Career Navigator (Streamlit + Neo4j + Ollama)

Run:  streamlit run app.py
Needs career_navigator.py in the same folder, seed.cypher already loaded,
and Ollama running with the model below pulled.
"""
import json
import os

import fitz  # pymupdf
import ollama
import streamlit as st

import pandas as pd

from career_navigator import analyze, driver, mark_completed, save_profile

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

st.set_page_config(page_title="Career Navigator", page_icon="🧭", layout="wide")
st.markdown("""
<style>
.stApp {
  background:
    radial-gradient(1100px 560px at 8% -10%, #4b2fd655, transparent),
    radial-gradient(900px 500px at 100% 0%, #0ea5e955, transparent),
    #0b0f1f;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #141a33, #0d1226);
  border-right: 1px solid #ffffff14;
}
.hero {
  position: relative; overflow: hidden; padding: 28px 34px; margin-bottom: 20px;
  border-radius: 22px; box-shadow: 0 12px 40px #7c5cff55;
  background: linear-gradient(120deg, #7c5cff, #0ea5e9 60%, #22d3ee);
}
.hero h1 { margin: 0; font-size: 2.4rem; color: #fff; }
.hero p  { margin: 8px 0 0; color: #ffffffe0; font-size: 1.05rem; }
.hero::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 30%, #ffffff33 50%, transparent 70%);
  transform: translateX(-100%); animation: shine 4.5s infinite;
}
@keyframes shine { to { transform: translateX(100%); } }
div[data-testid="stMetric"] {
  background: #ffffff0d; border: 1px solid #ffffff1f; padding: 14px 18px;
  border-radius: 16px; backdrop-filter: blur(8px); transition: all .2s ease;
}
div[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: #7c5cff; }
div[data-testid="stExpander"] {
  background: #ffffff0a; border: 1px solid #ffffff1a; border-radius: 16px; overflow: hidden;
}
.stButton > button, .stDownloadButton > button {
  border-radius: 12px; border: 1px solid #7c5cff88; color: #fff; font-weight: 600;
  background: linear-gradient(120deg, #7c5cff, #0ea5e9); transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-2px); box-shadow: 0 6px 22px #7c5cff77; border-color: #fff; color: #fff;
}
button[data-baseweb="tab"] { font-weight: 600; font-size: 1rem; }
.chip {
  display: inline-block; padding: 4px 13px; margin: 3px; border-radius: 999px;
  background: #22d3ee22; border: 1px solid #22d3ee66; color: #9ff3ff; font-size: .85rem;
}
a.yt {
  display: inline-block; padding: 5px 13px; border-radius: 10px; font-size: .88rem;
  background: #ff000022; border: 1px solid #ff4d4d88; color: #ffb3b3 !important;
  text-decoration: none; transition: all .15s ease;
}
a.yt:hover { background: #ff000044; transform: translateY(-1px); }
</style>
<div class="hero">
  <h1>🧭 Career Navigator</h1>
  <p>Resume in. Skill gaps, learning order and an AI career guide out, powered by a Neo4j knowledge graph.</p>
</div>
""", unsafe_allow_html=True)


# ---------- Graph helpers ----------
def graph_list(query, key):
    with driver.session() as s:
        return [r[key] for r in s.run(query)]


def known_skills():
    return graph_list("MATCH (s:Skill) RETURN s.name AS n ORDER BY n", "n")


def known_roles():
    return graph_list("MATCH (r:JobRole) RETURN r.title AS n ORDER BY n", "n")


def owned_skills(pid="me"):
    with driver.session() as s:
        return [r["n"] for r in s.run(
            "MATCH (:Person {id:$pid})-[:HAS_SKILL]->(s:Skill) RETURN s.name AS n", pid=pid)]


def role_scores(pid="me"):
    """Importance-weighted fit (%) for every role in the graph."""
    q = """
    MATCH (r:JobRole)-[req:REQUIRES]->(s:Skill)
    OPTIONAL MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(s)
    WITH r, sum(req.importance) AS total,
         sum(CASE WHEN p IS NULL THEN 0 ELSE req.importance END) AS have
    RETURN r.title AS role, round(100.0 * have / total) AS pct
    ORDER BY pct DESC
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q, pid=pid)]


def path_dot(path):
    """Graphviz picture: green = you have it, orange = gap; arrows = prerequisite."""
    gaps = [g["skill"] for g in path]
    owned = set(owned_skills())
    with driver.session() as s:
        edges = [(r["a"], r["b"]) for r in s.run(
            "MATCH (a:Skill)-[:PREREQUISITE_OF]->(b:Skill) WHERE b.name IN $g "
            "RETURN a.name AS a, b.name AS b", g=gaps)]
    nodes = set(gaps) | {a for a, _ in edges}
    lines = ['digraph G { rankdir=LR; bgcolor="transparent"; '
             'node [shape=box, style="filled,rounded", fontname=Helvetica, color="#00000000"]; '
             'edge [color="#9aa4d6"];']
    for n in nodes:
        color = "#9be7a8" if n in owned else "#ffd29b"
        lines.append(f'"{n}" [fillcolor="{color}"];')
    for a, b in edges:
        lines.append(f'"{a}" -> "{b}";')
    lines.append("}")
    return "\n".join(lines)


# ---------- Resume extraction ----------
def pdf_to_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_profile(text, skills):
    """LLM picks only skills from our canonical list -> built-in normalization."""
    prompt = (
        "Read this resume. Return JSON: "
        '{"name": "<full name>", "skills": ["<skill>", ...]}. '
        "Only include skills from this allowed list that the resume clearly shows:\n"
        f"{json.dumps(skills)}\n\nRESUME:\n{text[:6000]}"
    )
    import re

    # 1) Keyword matching (instant, works even if the model is not ready)
    aliases = {
        "Cloud (AWS)": ["aws", "amazon web services"],
        "CI/CD": ["ci/cd", "github actions", "jenkins"],
        "Machine Learning": ["machine learning", "scikit-learn", "sklearn"],
        "Deep Learning": ["deep learning", "pytorch", "tensorflow", "keras"],
        "NLP": ["nlp", "natural language"],
        "HTML/CSS": ["html", "css"],
        "Node.js": ["node.js", "nodejs", "express.js"],
        "JavaScript": ["javascript", "js"],
        "Data Visualization": ["data visualization", "matplotlib", "seaborn", "tableau"],
        "Cybersecurity": ["cybersecurity", "cyber security", "pentest"],
        "Data Structures": ["data structures", "dsa"],
        "Kubernetes": ["kubernetes", "k8s"],
        "APIs": ["api", "apis", "rest"],
    }
    low = text.lower()
    found = set()
    for sk in skills:
        for term in aliases.get(sk, []) + [sk.lower()]:
            if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", low):
                found.add(sk)
                break
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = lines[0][:40] if lines else "Learner"

    # 2) LLM adds anything the keywords missed (skipped if Ollama is unavailable)
    try:
        out = ollama.chat(
            model=MODEL, format="json", messages=[{"role": "user", "content": prompt}]
        )["message"]["content"]
        data = json.loads(out)
        found |= {s for s in data.get("skills", []) if s in skills}  # drop hallucinations
        name = data.get("name") or name
    except Exception as e:
        st.warning(f"AI model not available, used keyword matching instead ({type(e).__name__}).")
    return name, sorted(found)


# ---------- Career-only chatbot ----------
SYSTEM = (
    "You are a career guidance assistant. Answer ONLY career-related questions "
    "(skills, jobs, resumes, interviews, learning paths). Use ONLY the CONTEXT "
    "below for skills, courses and links; never invent any. If the context does "
    "not contain the answer, say so. Be concise and encouraging.\n\nCONTEXT:\n"
)


def is_career_question(msg):
    out = ollama.chat(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": "Is this message about careers, jobs, skills, resumes, "
                       "interviews, studying or learning for work? "
                       f"Answer only YES or NO.\n\nMessage: {msg}",
        }],
    )["message"]["content"]
    return out.strip().upper().startswith("YES")


def stream_answer(history, context):
    msgs = [{"role": "system", "content": SYSTEM + json.dumps(context)}] + history[-6:]
    for chunk in ollama.chat(model=MODEL, messages=msgs, stream=True):
        yield chunk["message"]["content"]


# ---------- Sidebar: profile creation ----------
with st.sidebar:
    st.header("1. Your profile")
    pdf = st.file_uploader("Upload resume (PDF)", type="pdf")
    role = st.selectbox("Target role", known_roles())
    if st.button("Analyze my resume", type="primary", disabled=pdf is None):
        with st.spinner("Reading resume and updating graph..."):
            name, skills = extract_profile(pdf_to_text(pdf), known_skills())
            save_profile("me", name, {s: 3 for s in skills}, role)
            st.session_state.result = analyze("me")
            st.session_state.name, st.session_state.skills = name, skills
            st.session_state.chat = []

# ---------- Main area ----------
if "result" not in st.session_state:
    st.info("Upload your resume and pick a target role in the sidebar to begin.")
    st.stop()

res = st.session_state.result
tab1, tab2, tab3 = st.tabs(["📊 Skill gap & path", "🎯 Role fit", "💬 Career chat"])

with tab1:
    st.subheader(f"Hi {st.session_state.name}")
    st.markdown("**Skills found in your resume:**")
    chips = "".join(f'<span class="chip">{s}</span>' for s in st.session_state.skills)
    st.markdown(chips or "_none detected_", unsafe_allow_html=True)
    m = res["match"]
    if m:
        pct = int(100 * m["have"] / m["total"])
        st.metric(f"Match for {m['role']}", f"{pct}%", f"{m['have']}/{m['total']} required skills")
        st.progress(pct / 100)

    path = res["learning_path"]
    for g in path:  # CampusX videos first, other resources as alternatives
        g["resources"].sort(key=lambda r: 0 if (r["title"] or "").startswith("CampusX") else 1)
    total_h = sum(
        (g["resources"][0]["hours"] or 0)
        for g in path if g["resources"] and g["resources"][0]["title"]
    )
    hpw = st.slider("Hours you can study per week", 2, 30, 8)
    c1, c2 = st.columns(2)
    c1.metric("Total study time", f"{total_h} h")
    c2.metric("Estimated time to be job-ready", f"{-(-total_h // hpw)} weeks")

    st.markdown("**Skill map** (green = you have it, orange = gap, arrow = learn first)")
    st.graphviz_chart(path_dot(path))

    st.subheader("Your learning path (learn top to bottom)")
    plan = [f"# Learning plan for {st.session_state.name}", ""]
    for i, g in enumerate(path, 1):
        titles = ", ".join(r["title"] for r in g["resources"] if r["title"]) or "no resource yet"
        plan.append(f"{i}. {g['skill']}: {titles}")
        with st.expander(f"{i}. {g['skill']}  (importance {g['importance']})"):
            for j, r in enumerate(g["resources"]):
                if r["title"]:
                    a, b = st.columns([4, 1])
                    if r["title"].startswith("CampusX"):
                        a.markdown(
                            f'<a class="yt" href="{r["url"]}" target="_blank">▶ {r["title"]}</a>'
                            f' &nbsp; ~{r["hours"]}h',
                            unsafe_allow_html=True,
                        )
                    else:
                        a.markdown(f"[{r['title']}]({r['url']}) , ~{r['hours']}h")
                    if b.button("Done ✅", key=f"done_{i}_{j}"):
                        mark_completed("me", r["title"])
                        st.session_state.result = analyze("me")
                        st.rerun()
    st.download_button("⬇️ Download my plan", "\n".join(plan), "learning_plan.md")

with tab2:
    st.subheader("How well you fit each role")
    scores = role_scores("me")
    st.bar_chart(pd.DataFrame(scores).set_index("role")["pct"])
    st.success(f"Best current fit: {scores[0]['role']} ({int(scores[0]['pct'])}%)")

with tab3:
    for m_ in st.session_state.chat:
        st.chat_message(m_["role"]).write(m_["content"])
    q = st.chat_input("Ask about your career path...")
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        st.chat_message("user").write(q)
        with st.chat_message("assistant"):
            try:
                ok = is_career_question(q)
            except Exception:
                ok = None
            if ok is None:
                ans = "The AI model isn't ready yet. Please try again in a few minutes."
                st.write(ans)
            elif ok:
                ctx = {**res, "role_fit_percent": role_scores("me")}
                ans = st.write_stream(stream_answer(st.session_state.chat, ctx))
            else:
                ans = "I can only help with career-related questions, like skills, roles, resumes and learning paths."
                st.write(ans)
        st.session_state.chat.append({"role": "assistant", "content": ans})