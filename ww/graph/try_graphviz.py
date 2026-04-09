import graphviz  # type: ignore[reportMissingImports]

# Create a new directed graph with attributes
dot = graphviz.Digraph(comment="Advanced Example Graph", format="png")
dot.attr(rankdir="LR")
dot.attr("node", shape="box", style="filled", fillcolor="lightblue")
dot.attr("edge", color="blue")

# Add nodes with custom attributes
dot.node("A", "Start", shape="ellipse", fillcolor="green")
dot.node("B", "Process 1")
dot.node("C", "Decision", shape="diamond", fillcolor="yellow")
dot.node("D", "Process 2")
dot.node("E", "End", shape="ellipse", fillcolor="red")

# Add edges with labels and attributes
dot.edge("A", "B", label="Begin")
dot.edge("B", "C", label="Check")
dot.edge("C", "D", label="Yes", color="green")
dot.edge("C", "B", label="No", style="dashed", color="red")
dot.edge("D", "E", label="Finish")

# Create a subgraph (cluster)
sub = dot.subgraph(name="cluster_subprocess")
if sub is not None:
    with sub as s:
        s.attr(label="Subprocess", style="filled", color="lightgrey")
        s.node("F", "Sub Step 1")
        s.node("G", "Sub Step 2")
        s.edge("F", "G", label="Next")

# Connect main graph to subgraph
dot.edge("D", "F")

# Render and save the graph
dot.render("tmp/advanced_graph", view=True)

print("Graph rendered to 'tmp/advanced_graph.png'")
