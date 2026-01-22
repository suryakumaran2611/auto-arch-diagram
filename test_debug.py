from tools.svg_to_drawio import SVGPathParser
import re

test_path = (
    "M61,-2454.81C61,-2391.77 61,-2282 61,-2282 61,-2282 180.35,-2282 180.35,-2282"
)

print("Test path:", test_path)
print("Path length:", len(test_path))

NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

i = 0
while i < len(test_path):
    char = test_path[i]
    print(f"\nPosition {i}: char='{char}', isalpha={char.isalpha()}")

    if char.isalpha():
        command = char
        i += 1
        numbers = []
        while i < len(test_path):
            num_match = NUMBER_PATTERN.match(test_path, i)
            if num_match:
                num = float(num_match.group())
                numbers.append(num)
                print(f"  Found number: {num}")
                i = num_match.end()
            else:
                print(f"  No number at position {i}, breaking")
                break
        print(f"  Command: {command}, Numbers: {numbers}")
    else:
        i += 1

print("\n--- Using SVGPathParser.parse ---")
result = SVGPathParser.parse(test_path, 3025.0)
print("Result:", result)
