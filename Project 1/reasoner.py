import os
from sys import argv
from collections import namedtuple
from collections.abc import Sequence
from py4j.java_gateway import JavaGateway


Role = namedtuple('role', 'role node')
Concept = namedtuple('concept', 'name concept')


class Node(Sequence):
    NAME = 0
    def __init__(self, concepts=None, roles=None):
        self.name = Node.NAME
        Node.NAME += 1
        self.concepts = list() if concepts is None else concepts
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
    
    def get_all_conjunctions(self):
        conjunctions = list()
        for c in self.concepts:
            conjunctions.extend(self.find_in_constituents(c))
        return conjunctions
    
    def find_in_constituents(self, concept):
        if concept.getClass().getSimpleName() == "ExistentialRoleRestriction":
            return self.find_in_constituents(concept.filler())
        if concept.getClass().getSimpleName() == "GeneralConceptInclusion":
            return self.find_in_constituents(concept.lhs()) + self.find_in_constituents(concept.rhs())
        if concept.getClass().getSimpleName() == "EquivalenceAxiom":
            return [c for con in concept.getConcepts() for c in self.find_in_constituents(con)]
        elif concept.getClass().getSimpleName() == "ConceptConjunction":
            return [concept] + [c for conj in concept.getConjuncts() for c in self.find_in_constituents(conj)]
        return list()


class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology
        self.axioms = Node(list(ontology.tbox().getAxioms()))
        self.conjunctions = self.axioms.get_all_conjunctions()
        self.elf = gateway.getELFactory()

    def find_subsumers(self, class_name):
        self.nodes = [Node([self.elf.getConceptName(class_name)])]
        self.changed = True
        while self.changed:
            self.changed = False
            self.update_nodes()

    def update_nodes(self):
        for node in self.nodes:
            self.conjunction_rule1(node)
            self.conjunction_rule2(node)
            self.existential_rule1(node)
            self.existential_rule2(node)
            self.subsumption_rule(node)

    def conjunction_rule1(self, node):
        # Add all concepts in conjunctions that are not currently part of the node
        for c in node.get_all_conjuncts():
            if c not in node:
                node.append(c)
                self.changed = True

    def conjunction_rule2(self, node):
        for i in range(len(node)):
            for j in range(len(node)):
                self.update_cnj2(node, self.elf.getConjunction(node[i], node[j]))
    
    def update_cnj2(self, node, conjunction):
        if self.should_update_cnj2(node, conjunction):
            self.changed = True
            node.append(conjunction)
    
    def should_update_cnj2(self, node, conjunction):
        return conjunction in self.conjunctions and conjunction not in node
    
    def existential_rule1(self, node):
        for exs in node.get_concepts_by_name('ExistentialRoleRestriction'):
            if self.should_update_ex1(exs, node.roles):
                self.update_ex1(exs, node.roles)
    
    def should_update_ex1(self, exs, roles):
        for role in roles:
            if exs.role() == role.role and exs.filler() in role.node:
                return False
        return True
    
    def update_ex1(self, exs, roles):
        self.changed = True
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
    
    def subsumption_rule(self, node):
        for gci in self.axioms.get_concepts_by_name("GeneralConceptInclusion"):
            if gci.lhs() in node and gci.rhs() not in node:
                node.append(gci.rhs())
                self.changed = True



if __name__ == "__main__":
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