const fs = require('fs');
const path = require('path');

const srcDir = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\src';
const outputFile = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\text_specification.md';

function extractTextFromFile(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    // Regex to match tags containing text, skipping ones with nested tags for simplicity.
    // E.g., <span className="text-sm">Hello</span>
    const regex = /<([a-zA-Z0-9_]+)[^>]*?(?:className=["']([^"']*)["'])?[^>]*?>([^<]+)<\/\1>/g;
    const results = [];
    let match;
    
    while ((match = regex.exec(content)) !== null) {
        const tag = match[1];
        const classes = match[2] || "";
        const text = match[3].trim();
        
        if (!text || text.startsWith('{') || text.length < 2) continue;
        
        const sizeClasses = classes.split(' ').filter(c => c.startsWith('text-') || c.startsWith('font-') || c.startsWith('leading-') || c.startsWith('tracking-'));
        const sizeSpec = sizeClasses.length ? sizeClasses.join(', ') : 'default/inherited size';
        
        results.push({ tag, text, classes: sizeSpec });
    }
    return results;
}

function walk(dir, filelist = []) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const filepath = path.join(dir, file);
        if (fs.statSync(filepath).isDirectory()) {
            filelist = walk(filepath, filelist);
        } else if (filepath.endsWith('.tsx') || filepath.endsWith('.jsx')) {
            filelist.push(filepath);
        }
    }
    return filelist;
}

const files = walk(srcDir);
let outputContent = '# Website Text Content and Specification\n\n';

for (const filepath of files) {
    const texts = extractTextFromFile(filepath);
    if (texts.length > 0) {
        const relPath = path.relative(srcDir, filepath);
        outputContent += `## Location: \`${relPath}\`\n\n`;
        outputContent += `| Text Content | Tag | Sizing/Font Specification |\n`;
        outputContent += `|---|---|---|\n`;
        for (const t of texts) {
            const cleanText = t.text.replace(/\n/g, ' ').replace(/\|/g, '\\|');
            outputContent += `| ${cleanText} | \`<${t.tag}>\` | ${t.classes} |\n`;
        }
        outputContent += `\n`;
    }
}

fs.writeFileSync(outputFile, outputContent, 'utf-8');
console.log('Extraction complete.');
