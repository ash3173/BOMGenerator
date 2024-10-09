import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

def extract_and_visualize_subgraph(graph, input_node, radius=None):
    # Step 1: Extract the subgraph with ego_graph function (nodes within the radius from the input node)
    subgraph = nx.ego_graph(graph, input_node, radius=radius)

    # Step 2: Position nodes for better visualization
    pos = nx.spring_layout(subgraph)

    # Step 3: Draw the subgraph
    fig, ax = plt.subplots(figsize=(10, 10))
    nx.draw(subgraph, pos, with_labels=True, node_size=700, node_color='lightgreen', 
            font_size=10, font_weight='bold', edge_color='gray', ax=ax)

    # Optionally add edge labels
    edge_labels = nx.get_edge_attributes(subgraph, 'weight')
    nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=edge_labels, ax=ax)

    # Display the subgraph
    ax.set_title(f'Subgraph Around Node {input_node} with Radius {radius}')
    st.pyplot(fig)

    return subgraph

def subgraph(graph):
    st.title("Subgraph Extraction and Visualization")

    # Step 1: Input for node ID
    input_node = st.text_input("Enter Node ID:", value='10')  # Default node ID is '10'

    # Step 2: Slider for radius
    radius = st.slider("Select Radius:", min_value=1, max_value=10, value=2)  # Default radius is 2

    if st.button("Visualize Subgraph"):
        # Step 3: Call the function to extract and visualize the subgraph
        try:
            subgraph = extract_and_visualize_subgraph(graph, input_node, radius)

            # Step 4: Display some subgraph info
            st.write(f"Subgraph Nodes: {list(subgraph.nodes())}")
            st.write(f"Subgraph Edges: {list(subgraph.edges())}")
        except nx.NetworkXError:
            st.error(f"Node {input_node} not found in the graph. Please enter a valid node ID.")