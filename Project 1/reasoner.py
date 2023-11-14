import os
from sys import argv
from py4j.java_gateway import JavaGateway

if len(argv) < 3:
    raise SyntaxError(f"""Missing ontology file and/or class name. Should call as:
                      \tpython {os.path.basename(__file__)} ONTOLOGY_FILE CLASS_NAME""")

gateway = JavaGateway()
formatter = gateway.getSimpleDLFormatter()
ontology = gateway.getOWLParser().parseFile(argv[1] if os.path.exists(argv[1]) else "pizza.owl")

# Change all conjunctions so that they have at most two conjuncts
gateway.convertToBinaryConjunctions(ontology)

elFactory = gateway.getELFactory()
concept_name = elFactory.getConceptName(argv[2])

# Using the reasoners
elk = gateway.getELKReasoner()
hermit = gateway.getHermiTReasoner() # might the upper case T!

elk.setOntology(ontology)
print(f"\nAccording to ELK, {concept_name} has the following subsumers: ")
subsumers = elk.getSubsumers(concept_name)
for concept in subsumers:
    print(" - ",formatter.format(concept))
print("(",len(subsumers)," in total)")