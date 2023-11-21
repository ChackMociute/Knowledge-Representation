import os
from sys import argv
from collections import namedtuple
from collections.abc import Sequence
from random import sample
from py4j.java_gateway import JavaGateway


gateway = JavaGateway()
formatter = gateway.getSimpleDLFormatter()

Role = namedtuple('role', 'role node')
Concept = namedtuple('concept', 'name concept')


class Node(Sequence):
    NAME = 0
    def __init__(self, elf, concepts=None, roles=None):
        self.name = Node.NAME
        Node.NAME += 1
        self.elf = elf
        self.concepts = list() if concepts is None else concepts
        self.roles = list() if roles is None else roles
        # if elf.getTop() not in self.concepts:
        #     self.concepts.append(elf.getTop())
    
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
    
    # Returns a list of all conjunctions found in any place in any concept in the node
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
    
    def convert_equivalence_to_subsumption(self):
        for x, y in map(lambda x: x.getConcepts(), self.get_concepts_by_name("EquivalenceAxiom")):
            self.concepts.extend([self.elf.getGCI(x, y), self.elf.getGCI(y, x)])


class ELReasoner:
    def __init__(self, ontology, rule_order='random'):
        self.ontology = ontology
        self.elf = gateway.getELFactory()
        self.axioms = Node(self.elf, list(ontology.tbox().getAxioms()))
        self.axioms.convert_equivalence_to_subsumption()
        self.conjunctions = self.axioms.get_all_conjunctions()
        self.rules = [self.conjunction_rule1, self.conjunction_rule2,
                      self.existential_rule1, self.existential_rule2,
                      self.subsumption_rule]
        self.rule_order = rule_order

    def find_subsumers(self, class_name):
        self.nodes = [Node(self.elf, [self.elf.getConceptName(class_name)])]
        self.changed = True
        while self.changed:
            self.changed = False
            self.update_nodes()

    def update_nodes(self):
        for node in self.nodes:
            for i in sample(range(len(self.rules)), k=len(self.rules))\
                if self.rule_order == "random" else self.rule_order:
                self.rules[i](node)

    def conjunction_rule1(self, node):
        # Add all concepts in conjunctions that are not currently part of the node
        for c in node.get_all_conjuncts():
            if c not in node:
                node.append(c)
                self.changed = True

    def conjunction_rule2(self, node):
        # Add conjunctions to the node which can be found in the TBox
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
    
    # Return false if a role to a concept already exists. True otherwise
    def should_update_ex1(self, exs, roles):
        for role in roles:
            if exs.role() == role.role and exs.filler() in role.node:
                return False
        return True
    
    def update_ex1(self, exs, roles):
        self.changed = True
        # If a node with appropriate concept already exists, add a role connection to it
        for n in self.nodes:
            if exs.filler() in n:
                roles.append(Role(exs.role(), n))
                return
        # Otherwise create a new node
        node = Node(self.elf, [exs.filler()])
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
    
    ontology = gateway.getOWLParser().parseFile(argv[1] if os.path.exists(argv[1]) else "pizza.owl")

    # Change all conjunctions so that they have at most two conjuncts
    gateway.convertToBinaryConjunctions(ontology)
    
    reasoner = ELReasoner(ontology)
    reasoner.find_subsumers(argv[2])

    for subsumer in reasoner.nodes[0]:
        print(subsumer)