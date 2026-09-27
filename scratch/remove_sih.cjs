const fs = require('fs');
const path = require('path');

const srcDir = 'c:\\Users\\DELL\\Desktop\\fe duplicate\\src';

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

for (const filepath of files) {
    let content = fs.readFileSync(filepath, 'utf-8');
    let original = content;

    // Remove SIH26031 strings
    // E.g., " Project Code: SIH26031" -> " Project Code: "
    // "SIH26031 CORE MVP" -> "CORE MVP"
    // "— SIH26031" -> "— "
    content = content.replace(/SIH26031/g, '');
    
    // Clean up empty spans or weird formatting left behind
    content = content.replace(/Project Code: \s*/g, 'Project Code: ');
    content = content.replace(/— \s*<\//g, '</');

    if (content !== original) {
        fs.writeFileSync(filepath, content, 'utf-8');
    }
}
console.log('Removed SIH26031');
