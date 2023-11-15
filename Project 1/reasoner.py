import os
from sys import argv
from collections import namedtuple
from collections.abc import Sequence
from py4j.java_gateway import JavaGateway


Role = namedtuple('role', 'role node')
Concept = namedtuple('concept', 'name concept')


class Node(Sequence):
    NAME = 0
    def __init__(self, concepts=list(), roles=None):
        self.name = Node.NAME
        Node.NAME += 1
        self.concepts = concepts
        self.roles = list() if roles is None else roles
    
    def __getitem__(self, i):
        return self.concepts[i]
    
    def __len__(self):
        return len(self.concepts)
    
    def __repr__(self):
        return f'Node {self.name}:\n' + '\n'.join([formatter.format(c) for c in self.concepts])
    
    def append(self, item):
        self.concepts.append(item)
    
    def get_concepts_by_name(self, name):
        return [c for n, c in self.get_named_concepts() if n == name]

    def get_named_concepts(self):
        return [Concept(c.getClass().getSimpleName(), c) for c in self.concepts]
    
    def get_all_conjuncts(self):
        return [con for c in self.get_concepts_by_name('ConceptConjunction')
                for con in c.getConjuncts()]


class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology
        self.axioms = ontology.tbox().getAxioms()
        self.elf = gateway.getELFactory()

    def find_subsumers(self, class_name):
        self.nodes = [Node([
            self.elf.getConjunction(self.elf.getConceptName(class_name), self.elf.getConceptName('A')),
            self.elf.getExistentialRoleRestriction(self.elf.getRole('r'), self.elf.getConjunction(self.elf.getConceptName('B'), self.elf.getConceptName('C')))])]
        # self.nodes = [Node(0, [self.elf.getConceptName(class_name)])]
        self.changed = True
        while self.changed:
            self.changed = False
            self.update_nodes()

    def update_nodes(self):
        for node in self.nodes:
            self.conjunction_rule1(node)
            self.existential_rule1(node)
            self.existential_rule2(node)

    def conjunction_rule1(self, node):
        # Add all concepts in conjunctions that are not currently part of the node
        for c in node.get_all_conjuncts():
            if c not in node:
                node.append(c)
                self.changed = True
    
    def existential_rule1(self, node):
        for exs in node.get_concepts_by_name('ExistentialRoleRestriction'):
            if self.should_update(exs, node.roles):
                self.update(exs, node.roles)
    
    def should_update_ex1(self, exs, roles):
        for role in roles:
            if exs.role() == role.role and exs.filler() in role.node:
                return False
        return True
    
    def update_ex1(self, exs, roles):
        for n in self.nodes:
            if exs.filler() in n:
                roles.append(Role(exs.role, n))
                return
        node = Node([exs.filler()])
        self.nodes.append(node)
        roles.append(Role(exs.role(), node))
    
    def existential_rule2(self, node):
        for r in node.roles:
            for c in r.node:
                self.update_ex2(self.elf.getExistentialRoleRestriction(r.role, c), node)
    
    def update_ex2(self, existential, node):
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

    for node in reasoner.nodes:
        print(node, '\n')