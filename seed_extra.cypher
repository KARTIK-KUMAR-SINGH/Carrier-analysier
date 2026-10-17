// Extra skills
UNWIND ['JavaScript','HTML/CSS','React','Node.js','Java','Excel','Pandas',
        'Data Visualization','Power BI','Docker','Cloud (AWS)','APIs','Data Structures']
AS name MERGE (:Skill {name: name});

// Extra prerequisites
UNWIND [
  ['HTML/CSS','JavaScript'],
  ['JavaScript','React'],
  ['JavaScript','Node.js'],
  ['Node.js','APIs'],
  ['Python','Pandas'],
  ['Pandas','Data Visualization'],
  ['Excel','Power BI'],
  ['Docker','Cloud (AWS)'],
  ['Docker','MLOps'],
  ['Data Structures','Machine Learning']
] AS pair
MATCH (a:Skill {name: pair[0]}), (b:Skill {name: pair[1]})
MERGE (a)-[:PREREQUISITE_OF]->(b);

// Roles and required skills
UNWIND [
  ['Web Developer', [['HTML/CSS',5],['JavaScript',5],['React',4],['Node.js',3],['Git',3],['APIs',3],['SQL',2]]],
  ['Data Analyst',  [['SQL',5],['Excel',4],['Python',4],['Pandas',4],['Data Visualization',4],['Power BI',3],['Statistics',3]]],
  ['Data Scientist',[['Python',5],['Pandas',5],['Statistics',5],['Machine Learning',5],['SQL',3],['Data Visualization',3]]]
] AS role
MERGE (r:JobRole {title: role[0]})
WITH r, role[1] AS reqs
UNWIND reqs AS q
MATCH (s:Skill {name: q[0]})
MERGE (r)-[x:REQUIRES]->(s) SET x.importance = q[1];

// Extra resources
UNWIND [
  ['freeCodeCamp Responsive Web Design',  'https://www.freecodecamp.org/learn/2022/responsive-web-design/', 30, 'HTML/CSS'],
  ['JavaScript.info',                     'https://javascript.info',                 40, 'JavaScript'],
  ['React Official Tutorial',             'https://react.dev/learn',                 20, 'React'],
  ['Node.js Learn',                       'https://nodejs.org/en/learn',             15, 'Node.js'],
  ['REST API Tutorial',                   'https://restfulapi.net',                  6,  'APIs'],
  ['Kaggle Learn Pandas',                 'https://www.kaggle.com/learn/pandas',     4,  'Pandas'],
  ['Kaggle Learn Data Visualization',     'https://www.kaggle.com/learn/data-visualization', 4, 'Data Visualization'],
  ['Microsoft Learn Power BI',            'https://learn.microsoft.com/en-us/training/powerplatform/power-bi/', 12, 'Power BI'],
  ['Microsoft Excel Training',            'https://support.microsoft.com/en-us/excel', 10, 'Excel'],
  ['Docker Getting Started',              'https://docs.docker.com/get-started/',    6,  'Docker'],
  ['AWS Cloud Practitioner Essentials',   'https://explore.skillbuilder.aws',        6,  'Cloud (AWS)'],
  ['CS50 Data Structures (CS50x)',        'https://cs50.harvard.edu/x',              40, 'Data Structures'],
  ['Kaggle Learn SQL',                    'https://www.kaggle.com/learn/intro-to-sql', 4, 'SQL'],
  ['Java Programming (MOOC.fi)',          'https://java-programming.mooc.fi',        50, 'Java']
] AS row
MATCH (s:Skill {name: row[3]})
MERGE (l:LearningResource {title: row[0]}) SET l.url = row[1], l.hours = row[2]
MERGE (l)-[:TEACHES]->(s);
