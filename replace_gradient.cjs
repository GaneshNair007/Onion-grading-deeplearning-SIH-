const fs = require('fs');
const path = require('path');

const filesToUpdate = [
  'src/sections/CoreStorySequence.tsx',
  'src/sections/FFTVisualization.tsx',
  'src/sections/LMSDashboard.tsx',
  'src/sections/CinematicHero.tsx',
  'src/sections/AIGradingReveal.tsx',
  'src/sections/FooterCTA.tsx',
  'src/pages/About.tsx',
  'src/pages/Prototype.tsx'
];

filesToUpdate.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');
    content = content.replace(/className="italic text-gradient-onion"/g, 'className=""');
    content = content.replace(/className="text-gradient-onion italic"/g, 'className=""');
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Updated ${file}`);
  } else {
    console.log(`File not found: ${file}`);
  }
});
