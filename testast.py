# analyze_ast.py — point this at sample_code.py

import ast

with open("test_codeast.py", "r") as f:
    source = f.read()

tree = ast.parse(source)

print("=" * 50)
print("CLASSES FOUND")
print("=" * 50)
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        print(f"\nCLASS: {node.name} (line {node.lineno})")
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                args = [a.arg for a in item.args.args]
                print(f"  METHOD: {item.name}({', '.join(args)}) → line {item.lineno}")

print("\n" + "=" * 50)
print("FUNCTIONS FOUND (top-level)")
print("=" * 50)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and not any(
        isinstance(parent, ast.ClassDef)
        for parent in ast.walk(tree)
        if node in ast.walk(parent) and parent is not node
    ):
        print(f"\nFUNCTION: {node.name}() (line {node.lineno})")

print("\n" + "=" * 50)
print("ALL FUNCTION CALLS")
print("=" * 50)
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            print(f"  {node.func.value.id if isinstance(node.func.value, ast.Name) else '?'}.{node.func.attr}() → line {node.lineno}")
        elif isinstance(node.func, ast.Name):
            print(f"  {node.func.id}() → line {node.lineno}")

print("\n" + "=" * 50)
print("IF CONDITIONS")
print("=" * 50)
for node in ast.walk(tree):
    if isinstance(node, ast.If):
        print(f"  IF at line {node.lineno}: {ast.unparse(node.test)}")

print("\n" + "=" * 50)
print("EXCEPTIONS RAISED")
print("=" * 50)
for node in ast.walk(tree):
    if isinstance(node, ast.Raise) and node.exc:
        print(f"  RAISE {ast.unparse(node.exc)} → line {node.lineno}")
