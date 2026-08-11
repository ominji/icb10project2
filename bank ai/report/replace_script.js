const fs = require('fs');
const p = 'money_magnet_dashboard.html';
const lines = fs.readFileSync(p, 'utf-8').split('\n');

const newLines = [];

for(let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    if (line.trim().startsWith('const originalCustomers = [')) {
        newLines.push('        let originalCustomers = [];');
        continue;
    }
    
    if (line.trim() === 'const state = {') {
        newLines.push('        let state = {');
        continue;
    }

    if (line.trim() === "window.addEventListener('DOMContentLoaded', () => {") {
        newLines.push("        window.addEventListener('DOMContentLoaded', async () => {");
        newLines.push(`            try {
                const response = await fetch('../customer_data_v2.csv');
                if (!response.ok) throw new Error('Data fetch failed');
                const csvText = await response.text();
                
                const csvLines = csvText.trim().split('\\n');
                const headers = csvLines[0].split(',').map(h => h.trim());
                
                originalCustomers = [];
                for(let j=1; j<csvLines.length; j++) {
                    const row = csvLines[j].trim();
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
                
                state.customers = JSON.parse(JSON.stringify(originalCustomers));
            } catch (err) {
                console.error("CSV 데이터를 불러오는데 실패했습니다.", err);
            }`);
        continue;
    }
    
    newLines.push(line);
}

fs.writeFileSync(p, newLines.join('\n'), 'utf-8');
console.log("Updated HTML correctly with Node line-by-line script.");
