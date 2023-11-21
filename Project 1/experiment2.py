import os
from reasoner import ELReasoner
from py4j.java_gateway import JavaGateway
from datetime import datetime
from random import choices

gateway = JavaGateway()
formatter = gateway.getSimpleDLFormatter()

ontologies = list()
for file in os.listdir('data/ontologies/'):
    ontology = gateway.getOWLParser().parseFile(os.path.join('data/ontologies/', file))
    gateway.convertToBinaryConjunctions(ontology)
    ontologies.append((ontology, [formatter.format(c) for c in choices(list(ontology.getConceptNames()), k=3)]))

def test_permutation(perm):
    for ont, concepts in ontologies:
        for c in concepts:
            reasoner = ELReasoner(ont, rule_order=perm)
            reasoner.find_subsumers(c)
            del(reasoner)
    
permutations = [(2,0,1,3,4), (2,0,1,4,3), (4,3,0,1,2), (4,3,1,0,2), (3,4,1,0,2)]
datapath = 'data/data2.csv'
with open(datapath, 'w') as f:
    f.write('permutation|time\n')
for permutation in permutations:
    for _ in range(20):
        start = datetime.now()
        test_permutation(permutation)
        with open(datapath, 'a') as f:
            f.write(f"{permutation}|{datetime.now() - start}\n")