import math

class TreeNode:
    def __init__(self, attribute=None, branches=None, label=None):
        self.attribute = attribute  # Attribute used for splitting
        self.branches = branches    # Dictionary of {attribute_value: child_node}
        self.label = label          # Label (class) assigned to leaf nodes

def entropy(x, y):
    if x == 0 or y == 0:
        return 0
    total = x + y
    return -((x/total) * math.log2(x/total) + (y/total) * math.log2(y/total))

def information_gain(entropy_S, splits):
    total_size = sum(sum(split.values()) for split in splits.values())
    remainder = sum((sum(split.values()) / total_size) * entropy(*split.values()) for split in splits.values())
    return entropy_S - remainder

def split_data(data, attribute_index):
    splits = {}
    for row in data:
        attribute_value = row[attribute_index]
        if attribute_value not in splits:
            splits[attribute_value] = {'+': 0, '-': 0}
        if row[3] == 'Tidak':
            splits[attribute_value]['-'] += 1
        else:
            splits[attribute_value]['+'] += 1
    return splits

def build_tree(data, attributes):
    # Calculate initial entropy of the entire dataset
    total = len(data)
    positive = sum(1 for row in data if row[3] == 'Ya')
    negative = total - positive
    entropy_S = entropy(positive, negative)

    # Base cases for recursion
    if entropy_S == 0:
        # All examples belong to the same class
        return TreeNode(label='Ya' if positive > 0 else 'Tidak')
    if not attributes:
        # No more attributes to split on
        return TreeNode(label='Ya' if positive >= negative else 'Tidak')

    # Calculate information gain for each attribute
    gains = {}
    for attribute_index in attributes:
        splits = split_data(data, attribute_index)
        gains[attribute_index] = information_gain(entropy_S, splits)

    # Select attribute with maximum information gain
    max_gain_attribute = max(gains, key=gains.get)
    max_gain_splits = split_data(data, max_gain_attribute)

    # Print information for each attribute
    for attribute_index in attributes:
        splits = split_data(data, attribute_index)
        attribute_name = ""
        if attribute_index == 0:
            attribute_name = "Cuaca"
        elif attribute_index == 1:
            attribute_name = "Temperatur"
        elif attribute_index == 2:
            attribute_name = "Kelembaban"

        print(f"Values({attribute_name}) = ", end="")
        for value in splits.keys():
            print(f"{value}, ", end="")
        print()

        print(f"S           = [{positive}+, {negative}-] |S|      = {total}")
        for key, split in splits.items():
            print(f"{key}      = [{split['+']}+, {split['-']}-] |{key}| = {sum(split.values())}")
            print(f"Entropy({key})             = {entropy(*split.values())}")
        print()

        # Print Gain for current attribute
        print(f"Gain({attribute_name})                     = {gains[attribute_index]}")
        print()

    # Remove selected attribute from list of attributes
    remaining_attributes = attributes.copy()
    remaining_attributes.remove(max_gain_attribute)

    # Recursively build branches of the tree
    branches = {}
    for attribute_value, split in max_gain_splits.items():
        subset_data = [row for row in data if row[max_gain_attribute] == attribute_value]
        branches[attribute_value] = build_tree(subset_data, remaining_attributes)

    return TreeNode(attribute=max_gain_attribute, branches=branches)

def print_tree(node, depth=0):
    if node.label:
        print('  ' * depth + 'Predict:', node.label)
    else:
        print('  ' * depth + 'Attribute:', node.attribute)
        for value, branch in node.branches.items():
            print('  ' * (depth + 1) + value + ' -> ', end='')
            print_tree(branch, depth + 1)

def main():
    table = """
    Cerah   Panas       Tinggi      Tidak
    Cerah   Panas       Normal      Tidak
    Mendung Panas       Tinggi      Ya
    Hujan   Sejuk       Tinggi      Ya
    Hujan   Dingin      Normal      Ya
    Hujan   Dingin      Normal      Tidak
    Mendung Dingin      Normal      Ya
    Cerah   Sejuk       Tinggi      Tidak
    Cerah   Dingin      Normal      Ya
    Hujan   Sejuk       Normal      Ya
    Cerah   Sejuk       Normal      Ya
    Mendung Sejuk       Tinggi      Ya
    Mendung Panas       Normal      Ya
    Hujan   Sejuk       Tinggi      Tidak
    """

    table = table.strip().split('\n')
    table = [x.split() for x in table]

    attributes = [0, 1, 2]  # Indexes of attributes Cuaca, Temperatur, Kelembaban

    tree = build_tree(table, attributes)
    print_tree(tree)

if __name__ == "__main__":
    main()
