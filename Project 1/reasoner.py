import os
from sys import argv
from py4j.java_gateway import JavaGateway

argv.extend(['potato_bowls.ttl', 'CheesyBowl'])

if len(argv) < 3:
    raise SyntaxError(f"""Missing ontology file and/or class name. Should call as:
                      \tpython {os.path.basename(__file__)} ONTOLOGY_FILE CLASS_NAME""")

gateway = JavaGateway()
formatter = gateway.getSimpleDLFormatter()
ontology = gateway.getOWLParser().parseFile(argv[1] if os.path.exists(argv[1]) else "pizza.owl")

# Change all conjunctions so that they have at most two conjuncts
gateway.convertToBinaryConjunctions(ontology)

axioms = ontology.tbox().getAxioms()
elf = gateway.getELFactory()

nodes = {0: [elf.getConjunction(elf.getConceptName(argv[2]), elf.getConceptName('A'))]}
changed = True

def update_nodes():
    changed = False
    for n, concepts in nodes.items():
        for concept in concepts:
            if concept.getClass().getSimpleName() == 'ConceptConjunction':
                for c in concept.getConjuncts():
                    if c not in concepts:
                        concepts.append(c)

while changed:
    changed = update_nodes()

for v in nodes[0]:
    print(formatter.format(v))