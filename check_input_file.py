import sys

if len(sys.argv) != 2:
    print("Usage: python check_input_file.py <filename>")
    sys.exit(1)

with open(sys.argv[1], "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if line.count("(") > line.count(")"):
            print(f"Unclosed parenthesis on line {line_num}: {line.strip()}")
