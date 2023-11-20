import os
from reasoner import ELReasoner
from py4j.java_gateway import JavaGateway
from itertools import permutations
from datetime import datetime

gateway = JavaGateway()
formatter = gateway.getSimpleDLFormatter()
ontology = gateway.getOWLParser().parseFile('potato_bowls.ttl')

# Change all conjunctions so that they have at most two conjuncts
gateway.convertToBinaryConjunctions(ontology)

concept = "PureDecadenceBowl"
datapath = 'data/data.csv'
with open(datapath, 'w') as f:
    f.write('permutation|time\n')
for permutation in permutations(range(5)):
    for _ in range(20):
        reasoner = ELReasoner(ontology, rule_order=permutation)
        start = datetime.now()
        reasoner.find_subsumers(concept)
        with open(datapath, 'a') as f:
            f.write(f"{permutation}|{datetime.now() - start}\n")