import re
import graphviz

def read_tex_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def extract_relationships(tex_content):
    pattern = r'\\subsubsection\*\{(.+?)\}\s*\n\s*(.+?)\s*~\\ensuremath\{\\sqsubseteq\}~\s*(.+)~'
    matches = re.findall(pattern, tex_content)
    return [(re.sub(r'\\ensuremath\{.*?\}', '', subclass).strip(),
             re.sub(r'\\ensuremath\{.*?\}', '', superclass).strip()) for subclass, _, superclass in matches]

def create_and_display_graph(relationships):
    dot = graphviz.Digraph(comment='Knowledge Tree', format='png')
    dot.graph_attr['size'] = '40.0!'  # Adjust the graph size (width, height in inches)
    dot.graph_attr['dpi'] = '450'  # DPI for higher resolution
    dot.graph_attr['rankdir'] = 'BT'  # Direction from bottom to top
    dot.graph_attr['ranksep'] = '2'


    for subclass, superclass in relationships:
        if superclass.startswith("~"):
            continue
        else:
            dot.node(subclass, subclass, fontname="Sans bold", fontsize='100', width='1', height='1')
            dot.node(superclass, superclass, fontname="Sans bold", fontsize='100', width='1', height='1')
            dot.edge(subclass, superclass,fontname="Sans bold")

    # Save and render the graph as a PNG image
    dot.render('knowledge_graph791', view=True)

file_path = 'Potatosscript.tex'
tex_content = read_tex_file(file_path)
relationships = extract_relationships(tex_content)
create_and_display_graph(relationships)
