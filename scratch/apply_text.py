import os
import re

src_dir = r"c:\Users\DELL\Desktop\fe duplicate\src"
old_spec = r"c:\Users\DELL\Desktop\fe duplicate\text_specification.md"
new_spec = r"c:\Users\DELL\Desktop\fe duplicate\text_specification_premium.md"

def parse_spec(filepath):
    data = {}
    current_loc = None
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            loc_match = re.match(r'## Location: `(.*?)`', line)
            if loc_match:
                current_loc = loc_match.group(1).replace('\\', '/')
                if current_loc not in data:
                    data[current_loc] = []
            elif line.startswith('|') and not line.startswith('| Text Content') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3 and current_loc:
                    text_content = parts[0].replace('\|', '|')
                    tag = parts[1].replace('`', '').replace('<', '').replace('>', '')
                    data[current_loc].append({'text': text_content, 'tag': tag})
    return data

old_data = parse_spec(old_spec)
new_data = parse_spec(new_spec)

changed_files = 0
for loc in old_data:
    if loc not in new_data:
        continue
    
    old_items = old_data[loc]
    new_items = new_data[loc]
    
    filepath = os.path.join(src_dir, loc)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original_content = content
    
    for i, old_item in enumerate(old_items):
        if i >= len(new_items):
            break
            
        old_t = old_item['text']
        new_t = new_items[i]['text']
        
        if old_t != new_t:
            # Create a regex to find the old text, ignoring whitespace differences
            # Escape regex characters except spaces
            escaped_old = re.escape(old_t)
            # Replace escaped spaces with \s+ to handle newlines/spaces in code
            pattern_str = escaped_old.replace(r'\ ', r'\s+')
            
            # Since sometimes it might have tags or something around it, we just replace the text
            # But what if there are multiple? We'll replace all for now, or just the first
            pattern = re.compile(pattern_str)
            
            new_content = pattern.sub(new_t.replace('\\', r'\\'), content)
            if new_content != content:
                print(f"Replaced in {loc}: '{old_t}' -> '{new_t}'")
                content = new_content
            else:
                print(f"Failed to find in {loc}: '{old_t}'")
                
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        changed_files += 1

print(f"Done. Changed {changed_files} files.")
