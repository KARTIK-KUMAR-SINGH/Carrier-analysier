// 10 more skills (total 32)
UNWIND ['Linux','CI/CD','Kubernetes','MongoDB','Flask','TypeScript',
        'Networking','System Design','Cybersecurity','C++'] AS name
MERGE (:Skill {name: name});

// Prerequisites
UNWIND [
  ['Linux','Docker'],
  ['Docker','Kubernetes'],
  ['Git','CI/CD'],
  ['Python','Flask'],
  ['JavaScript','TypeScript'],
  ['Networking','Cybersecurity'],
  ['Linux','Cybersecurity'],
  ['APIs','System Design']
] AS pair
MATCH (a:Skill {name: pair[0]}), (b:Skill {name: pair[1]})
MERGE (a)-[:PREREQUISITE_OF]->(b);

// 3 more roles (total 7)
UNWIND [
  ['Backend Developer',    [['Python',5],['APIs',5],['SQL',4],['Flask',3],['Docker',3],['Git',3],['System Design',3],['MongoDB',2]]],
  ['DevOps Engineer',      [['Linux',5],['Docker',5],['CI/CD',4],['Kubernetes',4],['Cloud (AWS)',4],['Git',3],['Python',3]]],
  ['Cybersecurity Analyst',[['Networking',5],['Linux',5],['Cybersecurity',5],['Python',3],['SQL',2]]]
] AS role
MERGE (r:JobRole {title: role[0]})
WITH r, role[1] AS reqs
UNWIND reqs AS q
MATCH (s:Skill {name: q[0]})
MERGE (r)-[x:REQUIRES]->(s) SET x.importance = q[1];

// Resources
UNWIND [
  ['Linux Journey',                 'https://linuxjourney.com',                                   15, 'Linux'],
  ['GitHub Actions Docs',           'https://docs.github.com/en/actions',                         8,  'CI/CD'],
  ['Kubernetes Basics Tutorial',    'https://kubernetes.io/docs/tutorials/kubernetes-basics/',    10, 'Kubernetes'],
  ['MongoDB University',            'https://learn.mongodb.com',                                  10, 'MongoDB'],
  ['Flask Quickstart',              'https://flask.palletsprojects.com/en/stable/quickstart/',    5,  'Flask'],
  ['TypeScript Handbook',           'https://www.typescriptlang.org/docs/handbook/intro.html',    12, 'TypeScript'],
  ['Professor Messer Network+',     'https://www.professormesser.com/network-plus/',              25, 'Networking'],
  ['System Design Primer',          'https://github.com/donnemartin/system-design-primer',        30, 'System Design'],
  ['TryHackMe Pre-Security',        'https://tryhackme.com',                                      20, 'Cybersecurity'],
  ['learncpp.com',                  'https://www.learncpp.com',                                   45, 'C++']
] AS row
MATCH (s:Skill {name: row[3]})
MERGE (l:LearningResource {title: row[0]}) SET l.url = row[1], l.hours = row[2]
MERGE (l)-[:TEACHES]->(s);
