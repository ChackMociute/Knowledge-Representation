import os
from sys import argv
from collections import namedtuple
from collections.abc import Sequence
from py4j.java_gateway import JavaGateway


Role = namedtuple('role', 'role node')

class Node(Sequence):
    def __init__(self, name, concepts=list(), roles=list()):
        self.name = name
        self.concepts = concepts
        self.roles = roles
    
    def __getitem__(self, i):
        return self.concepts[i]
    
    def __len__(self):
        return len(self.concepts)
    
    def append(self, item):
        self.concepts.append(item)

class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology
        self.axioms = ontology.tbox().getAxioms()
        self.elf = gateway.getELFactory()

    def find_subsumers(self, class_name):
        self.nodes = [Node(0, [self.elf.getConjunction(self.elf.getConceptName(class_name), self.elf.getConceptName('A'))], [Role('r', self.elf.getConceptName('A'))])]
        # self.nodes = [Node(0, [self.elf.getConceptName(class_name)])]
        self.changed = True
        while self.changed:
            self.changed = False
            self.update_nodes()

    def update_nodes(self):
        for node in self.nodes:
            self.conjunction_rule1(node)
            self.existential_rule2(node)

    def conjunction_rule1(self, node):
        # Add all concepts in conjunctions that are not currently part of the node
        for c in [conjunct for c in node
                  if c.getClass().getSimpleName() == 'ConceptConjunction'
                  for conjunct in c.getConjuncts()]:
            if c not in node:
                node.append(c)
                self.changed = True
    
    def existential_rule2(self, node):
        for r in node.roles:
            existential = self.elf.getExistentialRoleRestriction(self.elf.getRole(r.role), r.node)
            if existential not in node:
                node.append(existential)
                self.changed = True



if __name__ == "__main__":
    argv.extend(['potato_bowls.ttl', 'CheesyBowl'])

    if len(argv) < 3:
        raise SyntaxError(f"""Missing ontology file and/or class name. Should call with:
                        \tpython {os.path.basename(__file__)} ONTOLOGY_FILE CLASS_NAME""")

    gateway = JavaGateway()
    formatter = gateway.getSimpleDLFormatter()
    ontology = gateway.getOWLParser().parseFile(argv[1] if os.path.exists(argv[1]) else "pizza.owl")

    # Change all conjunctions so that they have at most two conjuncts
    gateway.convertToBinaryConjunctions(ontology)

    reasoner = ELReasoner(ontology)
    reasoner.find_subsumers(argv[2])

    for v in reasoner.nodes[0]:
        print(formatter.format(v))