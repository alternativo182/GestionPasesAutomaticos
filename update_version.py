import re
import sys

if len(sys.argv) < 2:
    print("Usage: python update_version.py <new_version>")
    sys.exit(1)

new_version = sys.argv[1]
filepath = "utils/update_checker.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_content = re.sub(
    r'__version__\s*=\s*"[^"]*"', f'__version__ = "{new_version}"', content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Version updated to {new_version}")
