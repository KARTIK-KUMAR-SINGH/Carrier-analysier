// CampusX video links (opens CampusX channel search for the topic).
// Hours are rough estimates. Replace url with an exact playlist link anytime.
UNWIND [
  ['CampusX: Statistics videos',         'https://www.youtube.com/@campusx-official/search?query=statistics',         25, 'Statistics'],
  ['CampusX: Python videos',             'https://www.youtube.com/@campusx-official/search?query=python',             30, 'Python'],
  ['CampusX: SQL videos',                'https://www.youtube.com/@campusx-official/search?query=sql',                15, 'SQL'],
  ['CampusX: Machine Learning videos',   'https://www.youtube.com/@campusx-official/search?query=machine%20learning', 80, 'Machine Learning'],
  ['CampusX: Deep Learning videos',      'https://www.youtube.com/@campusx-official/search?query=deep%20learning',    70, 'Deep Learning'],
  ['CampusX: NLP videos',                'https://www.youtube.com/@campusx-official/search?query=nlp',                30, 'NLP'],
  ['CampusX: Pandas videos',             'https://www.youtube.com/@campusx-official/search?query=pandas',             12, 'Pandas'],
  ['CampusX: Data Visualization videos', 'https://www.youtube.com/@campusx-official/search?query=data%20visualization', 8, 'Data Visualization']
] AS row
MATCH (s:Skill {name: row[3]})
MERGE (l:LearningResource {title: row[0]}) SET l.url = row[1], l.hours = row[2]
MERGE (l)-[:TEACHES]->(s);
