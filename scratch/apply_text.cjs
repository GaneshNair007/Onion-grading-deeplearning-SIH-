const fs = require('fs');
const path = require('path');

const srcDir = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\src';
const oldSpec = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\text_specification.md';
const newSpec = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\text_specification_premium.md';

function parseSpec(filepath) {
    const data = {};
    let currentLoc = null;
    const content = fs.readFileSync(filepath, 'utf-8');
    const lines = content.split('\n');

    for (const line of lines) {
        const locMatch = line.match(/^## Location: `(.*?)`/);
        if (locMatch) {
            currentLoc = locMatch[1].replace(/\\/g, '/');
            if (!data[currentLoc]) {
                data[currentLoc] = [];
            }
        } else if (line.startsWith('|') && !line.startsWith('| Text Content') && !line.startsWith('|---')) {
            const parts = line.split('|').slice(1, -1).map(p => p.trim());
            if (parts.length >= 3 && currentLoc) {
                const textContent = parts[0].replace(/\\\|/g, '|');
                const tag = parts[1].replace(/[`<>]/g, '');
                data[currentLoc].push({ text: textContent, tag: tag });
            }
        }
    }
    return data;
}

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
};

const oldData = parseSpec(oldSpec);
const newData = parseSpec(newSpec);

let changedFiles = 0;

for (const loc of Object.keys(oldData)) {
    if (!newData[loc]) continue;

    const oldItems = oldData[loc];
    const newItems = newData[loc];
    
    const filepath = path.join(srcDir, loc);
    if (!fs.existsSync(filepath)) {
        console.log(`File not found: ${filepath}`);
        continue;
    }

    let content = fs.readFileSync(filepath, 'utf-8');
    const originalContent = content;

    for (let i = 0; i < oldItems.length; i++) {
        if (i >= newItems.length) break;

        let oldT = oldItems[i].text;
        let newT = newItems[i].text;

        if (oldT !== newT) {
            const escapedOld = escapeRegExp(oldT);
            const patternStr = escapedOld.replace(/\\\ /g, '\\s+');
            const pattern = new RegExp(patternStr);
            
            const newContent = content.replace(pattern, newT);
            
            if (newContent !== content) {
                console.log(`Replaced in ${loc}: '${oldT}' -> '${newT}'`);
                content = newContent;
            } else {
                console.log(`Failed to find in ${loc}: '${oldT}'`);
            }
        }
    }

    if (content !== originalContent) {
        fs.writeFileSync(filepath, content, 'utf-8');
        changedFiles++;
    }
}

console.log(`Done. Changed ${changedFiles} files.`);
