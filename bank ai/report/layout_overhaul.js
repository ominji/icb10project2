const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Font Fix (Inject global !important font rule and reliable import)
const fontImport = `@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css');
        * { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important; }`;
content = content.replace(/<style>/, `<style>\n        ${fontImport}`);

// Also fix the link tags if they exist to standard preload
content = content.replace(/<link rel="stylesheet"[^>]*pretendard[^>]*>/, '');

// 2. CSS adjustments
// Remove sidebar CSS
content = content.replace(/\.sidebar\s*\{[^}]+\}/, '');
content = content.replace(/\.app-container\s*\{[^}]+\}/, `.app-container {
            display: flex;
            flex-direction: column;
            width: 100%;
            min-height: 100vh;
            background-color: var(--bg-dark);
        }`);

// Add GNB and Dropdown CSS
const newCss = `
        #gnb {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #ffffff;
            padding: 0 24px;
            height: 64px;
            border-bottom: 1px solid var(--card-border);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .gnb-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .gnb-tabs {
            display: flex;
            gap: 8px;
            height: 100%;
        }
        .gnb-tabs .tab-btn {
            border: none;
            background: transparent;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            padding: 0 16px;
            height: 100%;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        .gnb-tabs .tab-btn.active {
            color: var(--text-main);
            border-bottom: 3px solid var(--primary);
        }
        .main-content {
            padding: 24px 32px;
            width: 100%;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .filter-dropdown-container {
            position: relative;
            display: inline-block;
        }
        .filter-toggle-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #ffffff;
            border: 1px solid var(--input-border);
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            color: var(--text-main);
            transition: 0.2s;
        }
        .filter-toggle-btn:hover { background: var(--bg-dark); }
        .filter-panel {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: #ffffff;
            border: 1px solid var(--card-border);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            padding: 20px;
            width: 800px;
            z-index: 999;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }
        .filter-panel.show {
            display: grid;
        }
`;
content = content.replace(/(\.main-content\s*\{[^}]+\})/, `${newCss}\n$1`);
content = content.replace(/\.main-content\s*\{[^}]+\}/, ''); // the replacement above just added it cleanly, now remove original .main-content

// 3. HTML Surgery
const oldSidebarRegex = /<aside class="sidebar">[\s\S]*?<\/aside>/;
const sidebarMatch = content.match(oldSidebarRegex);

if (sidebarMatch) {
    let sidebarHtml = sidebarMatch[0];
    
    // Extract Logo
    let logoHtml = sidebarHtml.match(/<div class="sidebar-logo"[^>]*>([\s\S]*?)<\/div>/)[0];
    // Clean up logo html for GNB (remove border bottom and flex-col)
    logoHtml = logoHtml.replace(/flex-direction:\s*column;/, 'flex-direction: row;').replace(/padding-bottom:\s*15px;\s*border-bottom:[^;]+;/, '');
    logoHtml = logoHtml.replace(/<p class="sidebar-subtitle"[^>]*>.*?<\/p>/, ''); // remove subtitle in GNB
    
    // Extract Filters
    let filtersHtml = sidebarHtml.match(/<section class="sidebar-section">([\s\S]*?)<\/section>/)[1];
    filtersHtml = filtersHtml.replace(/<div class="sidebar-title">.*?<\/div>/, ''); // remove title
    
    // Extract Tabs
    let tabsHtml = content.match(/<nav class="tabs-container">([\s\S]*?)<\/nav>/)[1];
    
    // Remove old tabs
    content = content.replace(/<nav class="tabs-container">[\s\S]*?<\/nav>/, '');
    
    // Build GNB
    const gnbHtml = `
    <!-- GNB -->
    <header id="gnb">
        <div class="gnb-left">
            ${logoHtml}
        </div>
        <nav class="gnb-tabs">
            ${tabsHtml}
        </nav>
    </header>
    `;
    
    // Replace sidebar with GNB (which sits inside app-container but outside main-content)
    content = content.replace(oldSidebarRegex, gnbHtml);
    
    // Inject Filter Dropdown into main-header
    const filterBtnHtml = `
        <div class="filter-dropdown-container">
            <button class="filter-toggle-btn" onclick="document.getElementById('filterPanel').classList.toggle('show')">
                🔍 고급 필터 <small>▼</small>
            </button>
            <div id="filterPanel" class="filter-panel">
                ${filtersHtml}
            </div>
        </div>
    `;
    
    content = content.replace(/<div class="header-meta">([\s\S]*?)<\/div>/, `<div class="header-meta" style="display: flex; gap: 16px; align-items: center;">$1 ${filterBtnHtml}</div>`);
}

// 4. Remove unneeded margins/paddings from main layout elements
content = content.replace(/<div style="font-size: 13.5px;[^>]+>/, '<div style="font-size: 14px; color: var(--text-muted); margin-bottom: 20px; font-weight: 500;">');

// Add a script at the bottom to handle closing the dropdown when clicking outside
const closeScript = `
<script>
    // Close filter dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const panel = document.getElementById('filterPanel');
        const btn = document.querySelector('.filter-toggle-btn');
        if (panel && panel.classList.contains('show')) {
            if (!panel.contains(event.target) && !btn.contains(event.target)) {
                panel.classList.remove('show');
            }
        }
    });
</script>
</body>`;
content = content.replace(/<\/body>/, closeScript);


fs.writeFileSync(filePath, content, 'utf-8');
console.log("Layout overhaul to GNB + Dropdown completed.");
