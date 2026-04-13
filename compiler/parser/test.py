#!/usr/bin/env python3
import sys
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from parser import parse_file
import json
from ..ir.ast_nodes import print_ast, node_to_dict

# Use the example.osc file in the same directory
example_path = os.path.join(script_dir, 'example.osc')
ast = parse_file(example_path)
print("=== AST Tree ===")
print(print_ast(ast))
print()
print("=== JSON Output ===")
print(json.dumps(node_to_dict(ast), indent=2))