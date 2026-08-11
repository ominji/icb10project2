const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Update text colors for higher contrast (Admin dashboard style)
content = content.replace(/--text-main:\s*#[a-zA-Z0-9]+;/g, '--text-main: #111827;');
content = content.replace(/--text-muted:\s*#[a-zA-Z0-9]+;/g, '--text-muted: #4b5563;');

// 2. Compact PB Cockpit Cards
const compactCss = `
        .cockpit-card {
            padding: 14px !important;
        }
        .cockpit-card-title {
            font-size: 14px !important;
            margin-bottom: 12px !important;
        }
        .cockpit-info-list {
            gap: 6px !important;
            font-size: 13px !important;
        }
        .cockpit-row-1 {
            gap: 12px !important;
        }
        .cockpit-step-title {
            font-size: 16px !important;
            margin-bottom: 12px !important;
        }
        .leakage-sign-item {
            padding: 8px 12px !important;
        }
        .leakage-sign-title {
            font-size: 12px !important;
        }
        .leakage-sign-val {
            font-size: 14px !important;
        }
        .search-container {
            padding: 14px 20px !important;
            margin-bottom: 16px !important;
        }
`;
content = content.replace('</style>', compactCss + '\n</style>');

// 3. Replace Hero Section with Compact Header & Global Summary Widgets
const oldHeroRegex = /<div style="padding: 40px 0 40px; text-align: left; position: relative;">[\s\S]*?<!-- Filter Panel moves here, position adjusted -->/;
const newHero = `
        <div style="padding: 20px 0 20px; text-align: left; position: relative;">
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <h2 style="font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px; margin-bottom: 4px;">📊 PB 관제 총괄 요약</h2>
                    <div style="font-size: 13px; color: var(--text-muted); font-weight: 500;">
                        ● 데이터 기준 시점 — <span id="currentDateSpan">2026-06-10</span>
                    </div>
                </div>
                
                <div style="position: relative;">
                    <button class="filter-toggle-btn" style="background: var(--text-main); color: white; border: none; padding: 10px 20px; font-size: 13.5px; border-radius: 6px; font-weight: 700;" onclick="document.getElementById('filterPanel').classList.toggle('show')">
                        🔍 스마트 타겟팅 필터
                    </button>
                    <!-- Filter Panel moves here, position adjusted -->
`;

if (content.match(oldHeroRegex)) {
    content = content.replace(oldHeroRegex, newHero);
}

// 4. Inject the Global Summary Widgets just above the filter panel
const summaryWidgetsHTML = `
            </div>
            
            <!-- 글로벌 요약 통계 위젯 -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 10px;">
                <div style="background: #ffffff; border: 1px solid var(--card-border); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 12.5px; color: var(--text-muted); font-weight: 600;">👥 총 관리 고객 수</span>
                    <span style="font-size: 20px; font-weight: 800; color: var(--text-main);" id="global_total_cust">0명</span>
                </div>
                <div style="background: #ffffff; border: 1px solid var(--card-border); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 12.5px; color: var(--text-muted); font-weight: 600;">⚠️ 자산 유출 고위험군 수</span>
                    <span style="font-size: 20px; font-weight: 800; color: var(--accent-red);" id="global_high_risk">0명</span>
                </div>
                <div style="background: #ffffff; border: 1px solid var(--card-border); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 12.5px; color: var(--text-muted); font-weight: 600;">💰 총 관리 자산 (AUM)</span>
                    <span style="font-size: 20px; font-weight: 800; color: var(--primary);" id="global_total_aum">₩0</span>
                </div>
            </div>
`;
// find where the filter panel starts and inject the summary widgets BEFORE the closing </div> of the flex container above.
// Actually, newHero ends with "<!-- Filter Panel moves here, position adjusted -->\n". The HTML immediately after is `<div id="filterPanel" class="filter-panel" style="...">`.
// Let's replace the whole header and inject the widgets in the right spot.

content = content.replace(/(<main class="main-content">.*?<div style="position: relative;">.*?<\/button>)\s*<!-- Filter Panel moves here, position adjusted -->\s*(<div id="filterPanel")/s, 
`$1
        <div id="filterPanel" class="filter-panel" style="top: 100%; right: 0; left: auto; margin-top: 8px; width: 800px;">
`); // Fix filter panel position

// Inject the widgets before the close of the top header area
const injectWidgetsBefore = `        <div class="filter-dropdown-container">`; // wait, this was removed previously.
// Let's just find the closing </div> of the top padding area.
const mainHeaderCloseRegex = /(<div style="padding: 20px 0 20px; text-align: left; position: relative;">[\s\S]*?<\/div>\s*<\/div>\s*<\/div>)/;
content = content.replace(mainHeaderCloseRegex, `$1\n${summaryWidgetsHTML}`);

// 5. Add JS to populate the Global Summary Widgets
const jsInjection = `
<script>
    // Populate Global Summary Widgets
    function updateGlobalSummary() {
        const customers = state.filteredCustomers || originalCustomers;
        
        document.getElementById('global_total_cust').innerText = customers.length + '명';
        
        let highRiskCount = 0;
        let totalAum = 0;
        
        customers.forEach(c => {
            totalAum += c.Avg_Balance;
            if (getRiskLevel(c.Risk_Score) === '고위험') {
                highRiskCount++;
            }
        });
        
        document.getElementById('global_high_risk').innerText = highRiskCount + '명';
        document.getElementById('global_total_aum').innerText = formatWon(totalAum);
    }
    
    // Hook into applyFilters to update the summary whenever filters change
    const originalApplyFilters2 = typeof applyFilters === 'function' ? applyFilters : null;
    window.applyFilters = function() {
        if (originalApplyFilters2) {
            originalApplyFilters2();
        }
        updateGlobalSummary();
    };
    
    // Initial run
    setTimeout(updateGlobalSummary, 500);
</script>
</body>`;

content = content.replace('</body>', jsInjection);

fs.writeFileSync(filePath, content, 'utf-8');
console.log("High-density UI changes applied.");
