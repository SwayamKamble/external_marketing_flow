with open('c:/Users/lauki/OneDrive/Desktop/swayam final final/external_marketing_flow/frontend/src/pages/CreativeManager.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
import re

for idx, line in enumerate(lines):
    line_num = idx + 1
    tags = re.findall(r'(</div\s*>|<div\b)', line)
    for tag in tags:
        if tag.startswith('</'):
            if stack:
                stack.pop()
            else:
                print(f"Line {line_num}: Close div with empty stack! Text: {line.strip()}")
        else:
            is_self_closing = False
            pos = line.find('<div')
            while pos != -1:
                end_pos = line.find('>', pos)
                if end_pos != -1:
                    tag_content = line[pos:end_pos+1]
                    if tag_content.endswith('/>'):
                        is_self_closing = True
                pos = line.find('<div', pos+4)
            
            if not is_self_closing:
                stack.append((line_num, line.strip()))

print(f"Stack size at end: {len(stack)}")
if stack:
    print("Unclosed divs:")
    for num, text in stack:
        print(f"  Line {num}: {text[:100]}")
