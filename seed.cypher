// Constraints
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT role_title IF NOT EXISTS FOR (r:JobRole) REQUIRE r.title IS UNIQUE;
CREATE CONSTRAINT res_title IF NOT EXISTS FOR (l:LearningResource) REQUIRE l.title IS UNIQUE;

// Skills
UNWIND ['Python','SQL','Statistics','Linear Algebra','Machine Learning',
        'Deep Learning','NLP','MLOps','Git'] AS name
MERGE (:Skill {name: name});

// Prerequisites: (A)-[:PREREQUISITE_OF]->(B) means learn A before B
UNWIND [
  ['Python','Machine Learning'],
  ['Statistics','Machine Learning'],
  ['Linear Algebra','Machine Learning'],
  ['Machine Learning','Deep Learning'],
  ['Deep Learning','NLP'],
  ['Git','MLOps']
] AS pair
MATCH (a:Skill {name: pair[0]}), (b:Skill {name: pair[1]})
MERGE (a)-[:PREREQUISITE_OF]->(b);

// Job role and required skills
MERGE (r:JobRole {title: 'AI Engineer'})
WITH r
UNWIND [
  ['Python', 5], ['Machine Learning', 5], ['Deep Learning', 4],
  ['NLP', 3], ['MLOps', 3], ['SQL', 2]
] AS req
MATCH (s:Skill {name: req[0]})
MERGE (r)-[x:REQUIRES]->(s) SET x.importance = req[1];

// Learning resources
UNWIND [
  ['Python for Everybody',            'https://www.py4e.com',                   20, 'Python'],
  ['Khan Academy Statistics',         'https://www.khanacademy.org/math/statistics-probability', 25, 'Statistics'],
  ['3Blue1Brown Linear Algebra',      'https://www.3blue1brown.com',            10, 'Linear Algebra'],
  ['Andrew Ng ML Specialization',     'https://www.coursera.org/specializations/machine-learning-introduction', 60, 'Machine Learning'],
  ['fast.ai Practical Deep Learning', 'https://course.fast.ai',                 40, 'Deep Learning'],
  ['Hugging Face NLP Course',         'https://huggingface.co/learn/nlp-course', 30, 'NLP'],
  ['Pro Git Book',                    'https://git-scm.com/book',               8,  'Git'],
  ['Made With ML (MLOps)',            'https://madewithml.com',                 25, 'MLOps']
] AS row
MATCH (s:Skill {name: row[3]})
MERGE (l:LearningResource {title: row[0]}) SET l.url = row[1], l.hours = row[2]
MERGE (l)-[:TEACHES]->(s);

// Sample learner
MERGE (p:Person {id: 'u1'}) SET p.name = 'Asha'
WITH p
MATCH (py:Skill {name:'Python'}), (sq:Skill {name:'SQL'}), (r:JobRole {title:'AI Engineer'})
MERGE (p)-[:HAS_SKILL {level: 3}]->(py)
MERGE (p)-[:HAS_SKILL {level: 2}]->(sq)
MERGE (p)-[:WANTS_ROLE]->(r);
