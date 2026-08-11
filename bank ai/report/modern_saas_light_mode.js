const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. :root variables replacement using regex to ignore exact whitespace
content = content.replace(/:root\s*\{[^}]*\}/s, `:root {
            --primary: #10b981;
            --primary-light: #d1fae5;
            --primary-dark: #059669;
            --bg-dark: #f9fafb; /* Off-white background */
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #e5e7eb;
            --text-main: #111827;
            --text-muted: #6b7280;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-green: #10b981;
            --input-bg: #ffffff;
            --input-border: #d1d5db;
        }`);

// 2. Remove radial gradients from body
content = content.replace(/background-image:\s*radial-gradient[^;]+;/g, '');

// 3. Clean up card styles (remove backdrop-filter and heavy shadows, add clean border-radius)
content = content.replace(/backdrop-filter:\s*blur\([^)]+\);/g, '');
content = content.replace(/box-shadow:\s*[^;]+;/g, 'box-shadow: none;');
// Add soft shadow instead to main cards if needed, or just let them have clean border
content = content.replace(/border-radius:\s*16px;/g, 'border-radius: 12px;');

// 4. Update specific background gradients (Dandi card)
content = content.replace(/background:\s*linear-gradient\(135deg,\s*rgba\(15,\s*27,\s*46,\s*0\.95\),\s*rgba\(8,\s*15,\s*25,\s*0\.98\)\);/g, 'background: #ffffff;');

// 5. Update header background gradient to solid or dark
content = content.replace(/background:\s*linear-gradient\(45deg,\s*#1e293b,\s*var\(--primary\)\);/g, 'color: #111827;');

// 6. Fix semi-transparent white text and borders
content = content.replace(/rgba\(255,\s*255,\s*255,\s*0\.[0-9]+\)/g, 'rgba(0, 0, 0, 0.05)');

// 7. Update JS Chart Configuration (colors and grid)
content = content.replace(/color:\s*'#94a3b8'/g, "color: '#6b7280'");
content = content.replace(/color:\s*'#f8fafc'/g, "color: '#111827'");
content = content.replace(/color:\s*'#ffffff'/g, "color: '#111827'");
content = content.replace(/rgba\(255,\s*255,\s*255,\s*0\.04\)/g, 'rgba(0, 0, 0, 0.04)');
content = content.replace(/rgba\(255,\s*255,\s*255,\s*0\.05\)/g, 'rgba(0, 0, 0, 0.05)');
content = content.replace(/borderColor:\s*'#0b131f'/g, "borderColor: '#ffffff'");
content = content.replace(/borderColor:\s*'#080f19'/g, "borderColor: '#ffffff'");

// Update scatter chart specifically for the mint green fill effect
content = content.replace(/backgroundColor:\s*'#00bda7'/g, "backgroundColor: 'rgba(16, 185, 129, 0.2)'");
content = content.replace(/backgroundColor:\s*'#00998f'/g, "backgroundColor: 'rgba(16, 185, 129, 0.2)'");
// The scatter chart line
content = content.replace(/borderColor:\s*'#00bda7'/g, "borderColor: '#10b981'");
content = content.replace(/borderColor:\s*'#00998f'/g, "borderColor: '#10b981'");

// 8. Fix input text colors and bg
content = content.replace(/color:\s*#ffffff;/g, 'color: var(--text-main);');
content = content.replace(/color:\s*var\(--text-main\);\s*color:\s*var\(--text-main\);/g, 'color: var(--text-main);'); // Cleanup if duplicated

// 9. Buttons
content = content.replace(/border-radius:\s*8px;/g, 'border-radius: 8px;');
// For .action-btn
content = content.replace(/background:\s*rgba\(0,\s*189,\s*167,\s*0\.1\);/g, 'background: var(--primary); color: #ffffff;');
content = content.replace(/background:\s*rgba\(0,\s*153,\s*143,\s*0\.1\);/g, 'background: var(--primary); color: #ffffff;');

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Modern SaaS Light Mode CSS updated!");
