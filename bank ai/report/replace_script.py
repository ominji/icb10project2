import os

file_path = 'money_magnet_dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False

for i, line in enumerate(lines):
    if line.strip().startswith('const originalCustomers = ['):
        new_lines.append('        let originalCustomers = [];\n')
        continue
    
    if line.strip() == 'const state = {':
        new_lines.append('        let state = {\n')
        continue

    if line.strip() == "window.addEventListener('DOMContentLoaded', () => {":
        new_lines.append("        window.addEventListener('DOMContentLoaded', async () => {\n")
        new_lines.append("""            try {
                const response = await fetch('../customer_data_v2.csv');
                if (!response.ok) throw new Error('Data fetch failed');
                const csvText = await response.text();
                
                const csvLines = csvText.trim().split('\\n');
                const headers = csvLines[0].split(',').map(h => h.trim());
                
                originalCustomers = [];
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
                
                state.customers = JSON.parse(JSON.stringify(originalCustomers));
            } catch (err) {
                console.error("CSV 데이터를 불러오는데 실패했습니다.", err);
            }
""")
        continue

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated HTML correctly.")
