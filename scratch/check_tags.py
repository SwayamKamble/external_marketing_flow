import re

with open('c:/Users/lauki/OneDrive/Desktop/swayam final final/external_marketing_flow/frontend/src/pages/CreativeManager.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's count divs from line 1829 to 2869
lines = content.splitlines()
subcontent = "\n".join(lines[1828:2868])

open_divs = len(re.findall(r'<div\b', subcontent))
close_divs = len(re.findall(r'</div>', subcontent))

print(f"Subcontent from line 1829 to 2868:")
print(f"Open divs: {open_divs}")
print(f"Close divs: {close_divs}")
print(f"Difference (Open - Close): {open_divs - close_divs}")

# Let's check opening and closing braces {}
open_braces = 0
close_braces = 0
for char in subcontent:
    if char == '{':
        open_braces += 1
    elif char == '}':
        close_braces += 1
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Difference (Open - Close): {open_braces - close_braces}")

# Let's check parentheses ()
open_parens = 0
close_parens = 0
for char in subcontent:
    if char == '(':
        open_parens += 1
    elif char == ')':
        close_parens += 1
print(f"Open parens: {open_parens}")
print(f"Close parens: {close_parens}")
print(f"Difference (Open - Close): {open_parens - close_parens}")
