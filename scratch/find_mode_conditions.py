with open('c:/Users/lauki/OneDrive/Desktop/swayam final final/external_marketing_flow/frontend/src/pages/CreativeManager.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'mode ===' in line:
        safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
        print(f"Line {idx+1}: {safe_line}")
