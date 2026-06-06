file_path = 'c:/Users/lauki/OneDrive/Desktop/swayam final final/external_marketing_flow/frontend/src/pages/CreativeManager.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines up to line 2573 (1-indexed, so index 2573)
keep_lines = lines[:2573]

# Append closing tags
closing_tags = [
    "      </div>\n",
    "    </div>\n",
    "  );\n",
    "}\n"
]

new_lines = keep_lines + closing_tags

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("CreativeManager.tsx cleaned up successfully!")
