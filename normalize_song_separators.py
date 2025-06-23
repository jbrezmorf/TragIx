from pathlib import Path
import sys


def process_file(input_path):
    lines = Path(input_path).read_text(encoding="utf-8").splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for incorrect sequences of "="
        if "=" in line:
            if line.strip("=") == "" and len(line) != 18:
                print(f"Line {i+1}: Incorrect number of '=' signs -> '{line}'")

        # Handle the correct line
        if line == "=" * 18:
            # Backtrack to find text_before
            j = len(new_lines) - 1
            # Remove empty lines before
            while j >= 0 and new_lines[j].strip() == "":
                j -= 1
            text_before = new_lines[j] if j >= 0 else ""
            new_lines = new_lines[: j + 1]
            new_lines.append("")  # Ensure one empty line
            new_lines.append("=" * 18)

            # Skip current line
            i += 1
            # Skip any empty lines after
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            # Add one empty line
            new_lines.append("")
            if i < len(lines):
                new_lines.append(lines[i])
                i += 1
            continue

        new_lines.append(line)
        i += 1

    # Save modified file
    Path(input_path).write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("File processing complete ✅")


# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_input_file.py <filename>")
        sys.exit(1)
    process_file(sys.argv[1])
