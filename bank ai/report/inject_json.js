const fs = require('fs');
const path = require('path');

const htmlPath = path.join(__dirname, 'money_magnet_dashboard.html');
const csvPath = path.join(__dirname, '..', 'customer_data_v2.csv');

// Read CSV
const csvText = fs.readFileSync(csvPath, 'utf-8');
const csvLines = csvText.trim().split('\n');
const headers = csvLines[0].split(',').map(h => h.trim());

const originalCustomers = [];
for(let i=1; i<csvLines.length; i++) {
    const row = csvLines[i].trim();
    if(!row) continue;
    const cols = row.split(',');
    let obj = {};
    headers.forEach((h, idx) => {
        let val = cols[idx];
        if(!isNaN(val) && val !== '') val = Number(val);
        obj[h] = val;
    });
    
    if(!obj.Risk_Level) {
        if(obj.Risk_Score >= 60) obj.Risk_Level = '고위험';
        else if(obj.Risk_Score >= 40) obj.Risk_Level = '중위험';
        else obj.Risk_Level = '저위험';
    }
    originalCustomers.push(obj);
}

const jsonString = JSON.stringify(originalCustomers);

let htmlContent = fs.readFileSync(htmlPath, 'utf-8');

// 1. Replace the empty array initialization
htmlContent = htmlContent.replace('let originalCustomers = [];', `let originalCustomers = ${jsonString};`);

// 2. Remove the fetch block from DOMContentLoaded
const fetchRegex = /try\s*\{\s*const response = await fetch\('\.\.\/customer_data_v2\.csv'\);[\s\S]*?originalCustomers\.push\(obj\);\s*\}/;
htmlContent = htmlContent.replace(fetchRegex, '');

fs.writeFileSync(htmlPath, htmlContent, 'utf-8');
console.log("Successfully injected JSON data back into HTML and removed fetch.");
