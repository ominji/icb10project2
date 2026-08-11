const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. :root variables
const rootOld = `        :root {
            --primary: #00bda7;
            --primary-light: #e2f1f0;
            --primary-dark: #008f7e;
            --bg-dark: #080f19;
            --sidebar-bg: #0c1625;
            --card-bg: rgba(15, 27, 46, 0.7);
            --card-border: rgba(0, 189, 167, 0.12);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-yellow: #fbbf24;
            --accent-red: #f87171;
            --accent-green: #34d399;
            --input-bg: #111e30;
            --input-border: #1e2e45;
        }`;
const rootNew = `        :root {
            --primary: #00998f;
            --primary-light: #e2f1f0;
            --primary-dark: #007a72;
            --bg-dark: #f4f7f6;
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #e2e8f0;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-green: #10b981;
            --input-bg: #f8fafc;
            --input-border: #cbd5e1;
        }`;
content = content.replace(rootOld, rootNew);

// 2. Body gradient
const bodyGradOld = `            background-image: radial-gradient(circle at 10% 20%, rgba(0, 189, 167, 0.04) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(0, 143, 126, 0.03) 0%, transparent 40%);`;
const bodyGradNew = `            background-image: radial-gradient(circle at 10% 20%, rgba(0, 153, 143, 0.02) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(0, 122, 114, 0.015) 0%, transparent 40%);`;
content = content.replace(bodyGradOld, bodyGradNew);

// 3. Replace white semi-transparent borders with black semi-transparent
content = content.split("rgba(255, 255, 255, 0.08)").join("rgba(0, 0, 0, 0.08)");
content = content.split("rgba(255, 255, 255, 0.05)").join("rgba(0, 0, 0, 0.05)");
content = content.split("rgba(255, 255, 255, 0.04)").join("rgba(0, 0, 0, 0.05)");
content = content.split("rgba(255, 255, 255, 0.1)").join("rgba(0, 0, 0, 0.1)");

// 4. Text colors hardcoded to #ffffff -> var(--text-main)
const dandiBgOld = "background: linear-gradient(135deg, rgba(15, 27, 46, 0.95), rgba(8, 15, 25, 0.98));";
const dandiBgNew = "background: #ffffff;";
content = content.replace(dandiBgOld, dandiBgNew);

const dandiBodyBgOld = "background: rgba(0, 0, 0, 0.25);";
const dandiBodyBgNew = "background: rgba(0, 153, 143, 0.05);";
content = content.replace(dandiBodyBgOld, dandiBodyBgNew);

// 5. Box shadows on cards
const cardShadowOld = "box-shadow: 0 4px 20px rgba(0, 189, 167, 0.05);";
const cardShadowNew = "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);";
content = content.split(cardShadowOld).join(cardShadowNew);

// 6. .header-title background
const headerTitleOld = "background: linear-gradient(45deg, #ffffff, var(--primary));";
const headerTitleNew = "background: linear-gradient(45deg, #1e293b, var(--primary));";
content = content.replace(headerTitleOld, headerTitleNew);

// 7. JS Chart options
content = content.split("color: '#94a3b8'").join("color: '#64748b'");
content = content.split("color: '#ffffff'").join("color: '#1e293b'");
content = content.split("borderColor: '#0b131f'").join("borderColor: '#ffffff'");

// 8. specific color fixes
content = content.split("color: #ffffff;").join("color: var(--text-main);");
content = content.split("color:#ffffff;").join("color: var(--text-main);");

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Conversion to light mode completed.");
