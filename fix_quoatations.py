import sys

# Define all double-quote characters we want to consider
QUOTE_CHARS = {'"', "“", "”", "„"}


# Helper to identify ranges of parentheses and ignore quotes inside them
def get_parentheses_ranges(text):
    stack = []
    ranges = []
    for i, c in enumerate(text):
        if c == "(":
            stack.append(i)
        elif c == ")" and stack:
            start = stack.pop()
            ranges.append((start, i))
    return ranges


def is_inside_parens(index, parens_ranges):
    return any(start <= index <= end for start, end in parens_ranges)


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_input_file.py <filename>")
        sys.exit(1)

    # Read the input
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    # Get the ranges to ignore
    parens_ranges = get_parentheses_ranges(text)

    # Search and process direct speech
    result = []
    in_quote = False

    i = 0
    while i < len(text):
        c = text[i]
        if c in QUOTE_CHARS and not is_inside_parens(i, parens_ranges):
            if not in_quote:
                # Start of a new quote
                in_quote = True
                result.append("\\uv{")
            else:
                # End of quote
                in_quote = False
                result.append("}")
            i += 1
        else:
            result.append(c)
            i += 1

    # Just in case quote was opened but never closed
    if in_quote:
        result.append("}")

    # Save the output
    with open(sys.argv[1] + "out.txt", "w", encoding="utf-8") as f:
        f.write("".join(result))

    print("Quotation marks processing complete ✅")


if __name__ == "__main__":
    main()
