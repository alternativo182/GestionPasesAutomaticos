import re
import sys

with open("utils/update_checker.py", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
if match:
    print(match.group(1))
else:
    print("0.0.0")
