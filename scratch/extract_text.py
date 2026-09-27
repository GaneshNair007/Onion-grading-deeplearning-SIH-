import os
import re

src_dir = r"c:\Users\DELL\Desktop\fe duplicate\src"
output_file = r"c:\Users\DELL\Desktop\fe duplicate\text_specification.md"

def extract_text_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find tags with text content: <Tag className="...">Text</Tag>
    # Very basic regex, misses nested but good enough for a report.
    matches = re.finditer(r'<([a-zA-Z0-9_]+)[^>]*?(?:className=["\'](.*?)["\'])?[^>]*?>([^<]+)</\1>', content)
    
    results = []
    for m in matches:
        tag = m.group(1)
        classes = m.group(2) or ""
        text = m.group(3).strip()
        
        # Skip empty or js expressions
        if not text or text.startswith('{') or len(text) < 2:
            continue
            
        # extract text size classes
        size_classes = [c for c in classes.split() if 'text-' in c or 'font-' in c or 'leading-' in c or 'tracking-' in c]
        size_spec = ", ".join(size_classes) if size_classes else "default/inherited size"
        
        results.append({
            'tag': tag,
            'text': text,
            'classes': size_spec
        })
    return results

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Website Text Content and Specification\n\n")
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.tsx', '.jsx')):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, src_dir)
                
                texts = extract_text_from_file(filepath)
                if texts:
                    out.write(f"## Location: `{rel_path}`\n\n")
                    out.write("| Text Content | Tag | Sizing/Font Specification |\n")
                    out.write("|---|---|---|\n")
                    for t in texts:
                        # Clean up text for markdown table
                        clean_text = t['text'].replace('\n', ' ').replace('|', '\|')
                        out.write(f"| {clean_text} | `<{t['tag']}>` | {t['classes']} |\n")
                    out.write("\n")

print("Done")
