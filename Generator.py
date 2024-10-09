import streamlit as st
import random
import csv
import math
from datetime import datetime, timedelta
import zipfile
import os
from io import BytesIO

# Define classes for MakeParts, PurchaseParts, Suppliers, Modules

class MakeParts:
    def __init__(self, part_id, parent_id):
        self.part_id = part_id
        self.part_name = f"MakePart_{part_id}"
        self.date_manufacturing = self.random_date()
        self.available_quantity = random.randint(100, 1000)
        self.manufacturing_cost = round(random.uniform(10, 100), 2)
        self.manufacturing_time = random.randint(1, 30)
        self.quality_control_status = random.choice(['Passed', 'Failed', 'Pending'])
        self.parent_id = parent_id
        self.label = "make parts"
        self.edge_weight = random.randint(10, 100)

    def random_date(self):
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 1, 1)
        time_between_dates = end_date - start_date
        random_number_of_days = random.randrange(time_between_dates.days)
        return start_date + timedelta(days=random_number_of_days)

    def to_csv_row(self):
        return [self.part_id, self.parent_id, self.part_name, self.date_manufacturing.strftime("%Y-%m-%d"),
                self.available_quantity, self.manufacturing_cost, self.manufacturing_time,
                self.quality_control_status, self.label, self.edge_weight]


class PurchaseParts:
    def __init__(self, part_id, parent_id, supplier_id):
        self.part_id = part_id
        self.part_name = f"PurchasePart_{part_id}"
        self.supplier_id = supplier_id
        self.date_purchased = self.random_date()
        self.available_quantity = random.randint(100, 1000)
        self.cost_per_unit = round(random.uniform(5, 50), 2)
        self.lead_time = random.randint(1, 30)
        self.warranty_period = random.randint(30, 365)
        self.parent_id = parent_id
        self.label = "Purchase_Parts"
        self.edge_weight = random.randint(10, 100)

    def random_date(self):
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 1, 1)
        time_between_dates = end_date - start_date
        random_number_of_days = random.randrange(time_between_dates.days)
        return start_date + timedelta(days=random_number_of_days)

    def to_csv_row(self):
        return [self.part_id, self.parent_id, self.part_name, self.supplier_id,
                self.date_purchased.strftime("%Y-%m-%d"), self.available_quantity,
                self.cost_per_unit, self.lead_time, self.label, self.edge_weight]


class Suppliers:
    def __init__(self, supplier_id, parent_id):
        self.supplier_id = supplier_id
        self.supplier_name = f"Supplier_{supplier_id}"
        self.contact_details = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        self.location = random.choice(['USA', 'China', 'Germany', 'Japan', 'UK'])
        self.label = "Suppliers"
        self.edge_weight = random.randint(10, 100)
        self.parent_id = parent_id

    def to_csv_row(self):
        return [self.supplier_id, self.parent_id, self.supplier_name, self.contact_details, self.location, '', '', '', self.label, self.edge_weight]


class Modules:
    def __init__(self, module_id, parent_id):
        self.module_id = module_id
        self.module_name = f"Module_{module_id}"
        self.label = "Module"
        self.edge_weight = random.randint(10, 100)
        self.parent_id = parent_id

    def to_csv_row(self):
        return [self.module_id, self.module_name, self.label, self.edge_weight, self.parent_id]



def create_zip(files):
    # Create an in-memory ZIP file
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for file in files:
            zf.write(file)
    memory_file.seek(0)
    return memory_file

# Function to expand graph and generate CSV
def expand_graph_csv(existing_nodes_level_3, total_new_nodes, levels_to_add):
    current_node_id = 1
    parent_ids = existing_nodes_level_3
    generated_files = []
    suppliers = {}

    factor = math.exp(math.log(total_new_nodes) / levels_to_add)
    num_modules = math.ceil(factor)*2

    csv_filename = "level_4_modules.csv"
    level_nodes = []
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Name', 'Label', 'Edge_weight', 'ParentID'])
        for i in range(num_modules):
            module = Modules(str(current_node_id), random.choice(parent_ids))
            writer.writerow(module.to_csv_row())
            level_nodes.append(current_node_id)
            current_node_id += 1

    generated_files.append(csv_filename)
    parent_ids = level_nodes

    for level in range(2, levels_to_add + 1):
        level_nodes = []
        nodes_in_this_level = min(math.ceil(factor ** level), total_new_nodes - current_node_id + 1)

        csv_filename = f"level_{level + 3}.csv"

        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'ParentID', 'Name', 'Attribute1', 'Attribute2', 'Attribute3', 'Attribute4', 'Attribute5', 'Label', 'Edge_Weight'])

            purchase_part_probability = min(0.4 + (level / levels_to_add) * 0.6, 1.0)

            for i in range(nodes_in_this_level):
                node_id = str(current_node_id)
                parent_id = random.choice(parent_ids)

                if random.random() <= purchase_part_probability:
                    supplier_id = f"S{current_node_id + 1}"  # Next ID will be for the supplier
                    node = PurchaseParts(node_id, parent_id, supplier_id)
                    writer.writerow(node.to_csv_row())
                    current_node_id += 1

                    # Create and write supplier node
                    supplier = Suppliers(supplier_id, node_id)  # Parent is the PurchaseParts node
                    writer.writerow(supplier.to_csv_row())
                    current_node_id += 1

                else:
                    node = MakeParts(node_id, parent_id)
                    writer.writerow(node.to_csv_row())
                    level_nodes.append(node_id)
                    current_node_id += 1

                if current_node_id > total_new_nodes:
                    break

        generated_files.append(csv_filename)
        parent_ids = level_nodes

        if current_node_id > total_new_nodes:
            break

    return generated_files


# Streamlit App Interface
st.title("Graph Expansion and CSV Generator")

# User input
existing_nodes = ['Kiyo Product Family - Series a', 'Kiyo Product Family - Series b', 'Kiyo Product Family - Series c', 'Kiyo Product Family - Series d', 'Kiyo Product Family - Series e', 'Kiyo Product Family - Series f', 'Coronus Product Family - Series a', 'Coronus Product Family - Series b', 'Coronus Product Family - Series c', 'Coronus Product Family - Series d', 'Coronus Product Family - Series e', 'Coronus Product Family - Series f',
                'Flex Product Family - Series a', 'Flex Product Family - Series b', 'Flex Product Family - Series c', 'Flex Product Family - Series d', 'Flex Product Family - Series e', 'Flex Product Family - Series f', 'Versys Metal Product Family - Series a', 'Versys Metal Product Family - Series b', 'Versys Metal Product Family - Series c', 'Versys Metal Product Family - Series d', 'Versys Metal Product Family - Series e', 'Versys Metal Product Family - Series f']
total_new_nodes = st.number_input("Total New Nodes", min_value=1, max_value=1000000, value=100000)
levels_to_add = st.number_input("Levels to Add", min_value=1, max_value=10, value=6)

if st.button('Generate Graph Data'):
    generated_files = expand_graph_csv(existing_nodes, total_new_nodes, levels_to_add)
    st.success(f"Generated {len(generated_files)} files")

    # Create ZIP file in memory
    zip_file = create_zip(generated_files)
    
    # Provide a download button
    st.download_button(
        label="Download All Files as ZIP",
        data=zip_file,
        file_name="graph_data.zip",
        mime="application/zip"
    )

