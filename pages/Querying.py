import streamlit as st
import networkx as nx
import csv
from datetime import datetime
import io
import matplotlib.pyplot as plt
import time
import tracemalloc
import warnings
import random

warnings.filterwarnings("ignore", category=DeprecationWarning)

def time_and_memory(func):
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.time()
        result = func(*args, **kwargs)  # Call the actual function
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Display time and memory used
        st.markdown(f"<span style='color:skyblue;'>Time taken: {end_time - start_time:.2f} seconds</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:skyblue;'>Memory used: {current / 1024:.2f} KiB</span>", unsafe_allow_html=True)

        
        return result  # Return the result of the wrapped function
    return wrapper
@time_and_memory
@st.cache_resource
def statistics(_graph):
    # Display graph statistics
    st.write(f"Number of nodes: {_graph.number_of_nodes()}")
    st.write(f"Number of edges: {_graph.number_of_edges()}")

@st.cache_resource
def extract_and_visualize_subgraph(_graph, input_node, radius=None):
    # Step 1: Extract the subgraph with ego_graph function (nodes within the radius from the input node)
    subgraph = nx.ego_graph(_graph, input_node, radius=radius)

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

@time_and_memory
def subgraph(_graph):
    st.title("Subgraph Extraction and Visualization")

    # Step 1: Check if sampled nodes are already in session state, if not, sample new nodes
    if 'sampled_nodes' not in st.session_state:
        all_nodes = list(_graph.nodes)[:1000]  # Get the first 1000 nodes
        # Sample 100 nodes, or fewer if there aren't enough nodes
        st.session_state.sampled_nodes = random.sample(all_nodes, min(100, len(all_nodes)))

    # Step 2: Selectbox for node ID from the sampled nodes
    input_node = st.selectbox("Select Node ID:", st.session_state.sampled_nodes)

    # Step 3: Slider for radius
    radius = st.slider("Select Radius:", min_value=1, max_value=10, value=2)  # Default radius is 2

    if st.button("Visualize Subgraph"):
        # Step 4: Call the function to extract and visualize the subgraph
        try:
            subgraph = extract_and_visualize_subgraph(_graph, input_node, radius)

            # Step 5: Display some subgraph info
            with st.expander("Show Subgraph Details"):
                st.write(f"Subgraph Nodes: {list(subgraph.nodes())}")
                st.write(f"Subgraph Edges: {list(subgraph.edges())}")
        except nx.NetworkXError:
            st.error(f"Node {input_node} not found in the graph. Please enter a valid node ID.")

@time_and_memory
def visualize_shortest_path(graph):
    # Get the list of all nodes in the graph
    node_list = list(graph.nodes())

    # Allow user to select the source and target nodes
    node_1 = st.text_input('Select the starting node (source)',value= 'Business Group')
    node_2 = st.text_input('Select the ending node (target)', value= '835')



    # Try to find the shortest path
    try:
        shortest_path = nx.shortest_path(graph, source=node_1, target=node_2)

        # Extract subgraph with nodes in the shortest path
        subgraph = graph.subgraph(shortest_path)

        # Draw the subgraph
        pos = nx.spring_layout(subgraph)
        plt.figure(figsize=(10, 6))
        nx.draw(subgraph, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10)

        # Highlight the edges in the shortest path
        path_edges = list(zip(shortest_path, shortest_path[1:]))
        nx.draw_networkx_edges(subgraph, pos, edgelist=path_edges, edge_color='r', width=2)

        # Show the plot in Streamlit
        st.pyplot(plt)

        # Display the shortest path in Streamlit
        st.write(f"The shortest path between `{node_1}` and `{node_2}` is: {shortest_path}")

    except nx.NetworkXNoPath:
        st.error(f"No path exists between `{node_1}` and `{node_2}`")


@time_and_memory
def calculate_total_cost_with_weights(graph):

    st.title("Total Cost Calculation for Manufacturing or Purchasing Parts")

    # Step 1: Filter nodes with the labels 'make_parts' or 'Purchase_Parts'
    valid_nodes = [node for node, data in graph.nodes(data=True) if data.get('label') in ['make parts', 'Purchase_Parts']]
    
    # Step 2: Randomly sample 100 nodes or less if there aren't enough
    if 'sampled_valid_nodes' not in st.session_state:
        st.session_state['sampled_valid_nodes'] = random.sample(valid_nodes, min(100, len(valid_nodes)))

    # Use the stored sampled nodes from session state
    sampled_valid_nodes = st.session_state['sampled_valid_nodes']

    # Step 3: Selectbox for valid nodes
    start_node = st.selectbox("Select the Start Node (Product Node):", sampled_valid_nodes)

    # Button to calculate the total cost
    if st.button("Calculate Total Cost"):
        if start_node:
            total_cost = 0
            visited = set()

            # Use a DFS to explore all nodes connected to the start_node
            stack = [start_node]

            while stack:
                node = stack.pop()

                if node in visited:
                    continue
                visited.add(node)

                # Get the label of the current node
                label = graph.nodes[node].get('label', '')

                # Add cost based on the node type
                if label == 'make_parts':
                    manufacturing_cost = graph.nodes[node].get('manufacturing_cost', 0)
                    total_cost += manufacturing_cost
                elif label == 'Purchase_Parts':
                    cost_per_unit = graph.nodes[node].get('cost_per_unit', 0)
                    available_quantity = graph.nodes[node].get('available_quantity', 0)
                    total_cost += cost_per_unit * available_quantity

                    # Add the edge weight (cost) to this node
                    for neighbor in graph.neighbors(node):
                        edge_weight = graph.edges[node, neighbor].get('weight', 0)
                        total_cost += edge_weight  # Add edge weight to total cost

                # Add connected nodes (children) to the stack to explore them
                for neighbor in graph.neighbors(node):
                    if neighbor not in visited:
                        stack.append(neighbor)

            # Display the total cost
            st.success(f"Total cost to manufacture or purchase parts for {start_node}: {total_cost}")
        else:
            st.warning("Please enter a valid start node.")


@time_and_memory
def count_parts_needed(graph):
    st.title("Parts Counter for Product Node")

    # Step 1: Filter nodes with labels 'make_parts' or 'Purchase_Parts'
    valid_nodes = [node for node, data in graph.nodes(data=True) if data.get('label') in ['make parts', 'Purchase_Parts', 'Module']]
    
    # Step 2: Randomly sample 100 nodes or less if there aren't enough
    if 'sampled_valid_nodes' not in st.session_state:
        st.session_state['sampled_valid_nodes'] = random.sample(valid_nodes, min(100, len(valid_nodes)))

    # Use the stored sampled nodes from session state
    sampled_valid_nodes = st.session_state['sampled_valid_nodes']

    # Step 3: Selectbox for valid nodes
    product_node = st.selectbox("Select the Product Node:", sampled_valid_nodes)

    # Button to calculate
    if st.button("Count Parts"):
        if product_node:
            # Labels of nodes
            labels = nx.get_node_attributes(graph, 'label')

            # Get the subgraph of connected nodes
            subgraph = nx.ego_graph(graph, product_node)  # Get all connected nodes

            # Initialize counters
            make_parts_count = 0
            purchase_parts_count = 0

            # Traverse the nodes in the subgraph
            for node in subgraph.nodes:
                if labels.get(node) == 'make_parts':
                    make_parts_count += 1
                elif labels.get(node) == 'Purchase_Parts':
                    purchase_parts_count += 1

            # Display the results
            st.write(f"Make parts needed: {make_parts_count}")
            st.write(f"Purchase parts needed: {purchase_parts_count}")
        else:
            st.write("Please select a valid product node.")


@time_and_memory
def check_part_expiration(graph):
    st.title("Part Expiration Checker")

    # Step 1: Filter nodes with the label 'make parts'
    make_parts_nodes = [node for node, data in graph.nodes(data=True) if data.get('label') == 'make parts']
    
    # Check if there are any 'make parts' nodes
    if not make_parts_nodes:
        st.warning("No nodes found with the label 'make parts'.")
        return  # Exit the function if there are no nodes

    # Check if 'sampled_expiry' exists in session state to avoid refreshing
    if 'sampled_expiry' not in st.session_state:
        # Randomly sample 100 nodes or fewer if there aren't enough
        st.session_state['sampled_expiry'] = random.sample(make_parts_nodes, min(100, len(make_parts_nodes)))

    # Use the stored sampled nodes from session state
    sampled_expiry = st.session_state['sampled_expiry']

    # Step 2: Selectbox for random sample of make_parts nodes
    part_node = st.selectbox("Select the Part Node ID:", sampled_expiry)

    # Step 3: Button to check if the part has expired
    if st.button("Check Expiration Status"):
        if part_node:
            if part_node in graph.nodes:
                manufacturing_date = graph.nodes[part_node].get('date_manufacturing', None)

                if manufacturing_date:
                    # Convert the manufacturing date to datetime object if it's not already
                    if isinstance(manufacturing_date, str):
                        manufacturing_date = datetime.strptime(manufacturing_date, "%Y-%m-%d")  # Assuming date is stored as 'YYYY-MM-DD'
                    
                    # Get the current date
                    current_date = datetime.now()

                    # Calculate the difference in days
                    time_difference = current_date - manufacturing_date

                    # Expiry check (if more than 1000 days have passed)
                    if time_difference.days > 1000:
                        st.success(f"The part {part_node} has expired.")
                    else:
                        st.success(f"The part {part_node} has not expired.")
                else:
                    st.warning(f"No manufacturing date available for part {part_node}.")
            else:
                st.error(f"Part {part_node} does not exist in the graph.")
        else:
            st.warning("Please select a valid part node.")


@time_and_memory
def find_suppliers_for_purchase_part(graph):
    # Step 1: Filter nodes with the label 'Purchase_Parts'
    purchase_parts_nodes = [node for node, data in graph.nodes(data=True) if data.get('label') == 'Purchase_Parts']
    
    # Check if 'sampled_purchase_parts' exists in session state to avoid refreshing
    if 'sampled_purchase_parts' not in st.session_state:
        st.session_state['sampled_purchase_parts'] = random.sample(purchase_parts_nodes, min(100, len(purchase_parts_nodes)))

    # Use the stored sampled nodes from session state
    sampled_purchase_parts = st.session_state['sampled_purchase_parts']

    # Step 2: Selectbox for random sample of Purchase_Parts nodes
    purchase_part_node = st.selectbox("Select Purchase Part Node ID:", sampled_purchase_parts)

    # Step 3: Button to find suppliers
    if st.button("Find Suppliers"):
        if not purchase_part_node:
            st.warning("Please select a valid Purchase Part Node ID.")
            return

        # Check if the purchase part node exists in the graph
        if purchase_part_node not in graph:
            st.warning(f"Node {purchase_part_node} not found in the graph.")
            return

        suppliers = []

        # Iterate through neighbors of the purchase part node
        for neighbor in graph.neighbors(purchase_part_node):
            # Check if the neighbor has the 'label' attribute indicating it is a supplier
            if graph.nodes[neighbor].get('label') == 'Suppliers':
                suppliers.append(neighbor)

        # Step 4: Display results
        if suppliers:
            st.success(f"Suppliers for {purchase_part_node}: {', '.join(suppliers)}")
        else:
            st.warning(f"No suppliers found for {purchase_part_node}.")


@time_and_memory
def get_quality_control_status_streamlit(graph):
    st.title("Check Quality Control Status")

    # Get all nodes with the label 'make parts'
    make_parts_nodes = [node for node, data in graph.nodes(data=True) if data.get('label') == 'make parts']
    
    # Check if 'sampled_quality' exists in session state to avoid refreshing
    if 'sampled_quality' not in st.session_state:
        st.session_state['sampled_quality'] = random.sample(make_parts_nodes, min(100, len(make_parts_nodes)))

    # Use the stored sampled nodes from session state
    sampled_nodes = st.session_state['sampled_quality']

    # Dropdown to select from sampled 'make parts' nodes
    part_id = st.selectbox("Select the Part ID:", sampled_nodes)

    # Button to check quality control status
    if st.button("Check Quality Control") and part_id:
        # Check if the node exists in the graph
        if part_id in graph.nodes:
            # Check if the node has a quality control status
            node_data = graph.nodes[part_id]
            if 'quality_control_status' in node_data:
                st.success(f"Part ID: {part_id}, Quality Control Status: {node_data['quality_control_status']}")
            else:
                st.warning(f"Part ID: {part_id} does not have a quality control status attribute.")
        else:
            st.error(f"Part ID: {part_id} not found in the graph.")

@time_and_memory
def display_node_features(graph):
    st.title("Node Features Viewer")
    
    # Check if 'sampled_nodes' exists in session state
    if 'sampled_nodes' not in st.session_state:
        all_nodes = list(graph.nodes)
        # Sample only once and store in session state
        if len(all_nodes) >100:
            st.session_state['sampled_nodes'] = random.sample(all_nodes, 100)
        else:
            st.session_state['sampled_nodes']=all_nodes

    # Use the stored sampled nodes from session state
    sampled_nodes = st.session_state['sampled_nodes']
    
    # Use selectbox for displaying sampled node options
    node_id = st.selectbox("Select the Node ID:", sampled_nodes)

    # If a node is selected
    if st.button("Check Node Attributes") and node_id:
        # Check if the node exists in the graph
        if node_id in graph.nodes:
            # Fetch all node attributes
            node_attributes = graph.nodes[node_id]
            
            # Display the node attributes in Streamlit
            if node_attributes:
                st.subheader(f"Features for Node ID: {node_id}")
                for key, value in node_attributes.items():
                    st.write(f"**{key}**: {value}")
            else:
                st.warning(f"Node {node_id} has no attributes.")
        else:
            st.error(f"Node ID {node_id} not found in the graph.")
# @time_and_memory
@st.cache_resource
def add_nodes_from_csv(_graph, all_csv):
    module = True
    
    for csv_filename in all_csv:
    
        # Read CSV from memory (uploaded files)
        reader = csv.DictReader(io.StringIO(csv_filename.getvalue().decode('utf-8')))
        
        for row in reader:
            if module:
                node_id = row['ID']
                parent_id = row['ParentID'] if row['ParentID'] else None
                node_type = row['Label']
                edge_weight = row['Edge_weight']
                name = row['Name']

                # Add node with attributes
                _graph.add_node(node_id, name=name, label=node_type, edge_weight=edge_weight)
                if parent_id:
                    _graph.add_edge(parent_id, node_id, weight=edge_weight)
                continue

            node_id = row['ID']
            parent_id = row['ParentID'] if row['ParentID'] else None
            node_type = row['Label']

            # Common attributes
            attributes = {
                'name': row['Name'],
                'label': node_type,
                'edge_weight': int(row['Edge_Weight'])
            }

            # Add type-specific attributes
            if node_type == 'make parts':
                attributes.update({
                    'date_manufacturing': datetime.strptime(row['Attribute1'], '%Y-%m-%d'),
                    'available_quantity': int(row['Attribute2']),
                    'manufacturing_cost': float(row['Attribute3']),
                    'manufacturing_time': int(row['Attribute4']),
                    'quality_control_status': row['Attribute5']
                })

            elif node_type == 'Purchase_Parts':
                attributes.update({
                    'supplier_id': row['Attribute1'],
                    'date_purchased': datetime.strptime(row['Attribute2'], '%Y-%m-%d'),
                    'available_quantity': int(row['Attribute3']),
                    'cost_per_unit': float(row['Attribute4']),
                    'lead_time': int(row['Attribute5']),
                })

            elif node_type == 'Suppliers':
                attributes.update({
                    'contact_details': row['Attribute1'],
                    'location': row['Attribute2']
                })

            # Add node with attributes
            _graph.add_node(node_id, **attributes)
            
            # If the node has a parent, create an edge between the parent and the node
            if parent_id:
                _graph.add_edge(parent_id, node_id, weight=attributes['edge_weight'])

        module = False

    return _graph

# Streamlit app for querying
def app():
    st.title("Graph Querying Page")

    # Step 1: Upload CSV files
    uploaded_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

    # Initialize an empty graph
    G = nx.DiGraph()

    # Add the root node
    G.add_node("Business Group")

    # Add the second level nodes
    second_level_nodes = ["Kiyo Product Family", "Coronus Product Family", "Flex Product Family", "Versys Metal Product Family"]
    for node in second_level_nodes:
        G.add_node(node)
        G.add_edge("Business Group", node)

    # Add the third level nodes for each second level node
    for parent_node in second_level_nodes:
        for i in range(6):
            child_node = f"{parent_node} - Series {chr(ord('a') + i)}"
            G.add_node(child_node)
            G.add_edge(parent_node, child_node)

    # Step 2: Add nodes from uploaded CSVs
    if uploaded_files:
        st.success("CSV files uploaded successfully!")
        graph = add_nodes_from_csv(G, uploaded_files)
        st.success("Graph converted from CSV successfully!")

        

        options = ["Select an option","Statistics", "Subgraph", "Visualize Shortest Path", "Total Cost", "Expiry Date", "Find Supplier", "Quality Control Status", "Node Features"]
        selected_option = st.selectbox("Choose a query:", options)
        if selected_option == "Statistics":
            statistics(graph)
        elif selected_option == "Subgraph":
            subgraph(graph)
        elif selected_option == "Visualize Shortest Path":
            visualize_shortest_path(graph)
        # elif selected_option == "Count Parts":
        #     count_parts_needed(graph)
        elif selected_option=="Total Cost":
            calculate_total_cost_with_weights(graph)
        elif selected_option=="Expiry Date":
            check_part_expiration(graph)
        elif selected_option=="Find Supplier":
            find_suppliers_for_purchase_part(graph)
        elif selected_option=="Quality Control Status":
            get_quality_control_status_streamlit(graph)
        elif selected_option=="Node Features":
            display_node_features(graph)

    else:
        st.warning("Please upload CSV files to add nodes to the graph.")


# Run the app
if __name__ == "__main__":
    app()
