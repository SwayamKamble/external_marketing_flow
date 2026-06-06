with open('c:/Users/lauki/OneDrive/Desktop/swayam final final/external_marketing_flow/frontend/src/pages/CreativeManager.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_string = False
escaped = False
string_char = None
start_line = 0

for idx, line in enumerate(lines):
    line_num = idx + 1
    # Check for backticks/quotes
    i = 0
    while i < len(line):
        char = line[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == '\\':
            escaped = True
            i += 1
            continue
        if char == '`':
            if in_string and string_char == '`':
                in_string = False
                print(f"CLOSED template string starting at line {start_line} on line {line_num}")
            elif not in_string:
                in_string = True
                string_char = '`'
                start_line = line_num
                print(f"OPENED template string on line {line_num}")
        i += 1

if in_string:
    print(f"ERROR: Template string starting at line {start_line} was never closed!")
