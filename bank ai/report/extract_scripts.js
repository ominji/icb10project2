const fs = require('fs');

const htmlPath = 'money_magnet_dashboard.html';
const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

const scriptRegex = /<script>([\s\S]*?)<\/script>/gi;
let match;
let i = 1;
while ((match = scriptRegex.exec(htmlContent)) !== null) {
    fs.writeFileSync(`test_script_${i}.js`, match[1], 'utf-8');
    i++;
}
console.log(`Extracted ${i-1} scripts.`);
