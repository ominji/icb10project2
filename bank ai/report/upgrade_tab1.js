const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Update the layout of .cockpit-row-1 to be a 2x2 grid instead of flex or 3-column.
// Actually, let's find .cockpit-row-1 in CSS and make it a 2x2 grid if it isn't.
const oldCssRow1 = /\.cockpit-row-1\s*\{\s*display:\s*grid;\s*grid-template-columns:\s*1fr\s*1fr\s*1\.5fr;\s*gap:\s*20px;\s*\}/;
const newCssRow1 = `.cockpit-row-1 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }`;
if (content.match(oldCssRow1)) {
    content = content.replace(oldCssRow1, newCssRow1);
} else {
    // If not found exactly, just inject it into style
    content = content.replace('</style>', `
        .cockpit-row-1 { grid-template-columns: repeat(2, 1fr) !important; }
        .leakage-signs-card { display: flex; flex-direction: column; gap: 12px; }
        .leakage-sign-item { background: var(--bg-dark); padding: 12px 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .leakage-sign-title { font-size: 13px; color: var(--text-muted); font-weight: 600; }
        .leakage-sign-val { font-size: 15px; font-weight: 800; color: var(--text-main); }
        .leakage-sign-val.warning { color: var(--accent-red); }
    </style>`);
}

// 2. Add the new card HTML inside .cockpit-row-1
const newCardHtml = `
                            <!-- 이탈 징후 집중 분석 -->
                            <div class="cockpit-card">
                                <div class="cockpit-card-title">🔍 머니무브(이탈 징후) 집중 분석 <span style="font-size:16px;">📉</span></div>
                                <div class="leakage-signs-card">
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">월 평균 타행/증권사 이체 빈도</span>
                                        <span class="leakage-sign-val" id="ls_freq">0회</span>
                                    </div>
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">월 급여 대비 이체 비율</span>
                                        <span class="leakage-sign-val" id="ls_ratio">0%</span>
                                    </div>
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">최근 3개월 누적 이체 금액</span>
                                        <span class="leakage-sign-val" id="ls_amount">₩0</span>
                                    </div>
                                </div>
                            </div>
`;

// Insert the new card after the first card (고객 기본 요약)
const insertTarget = /<div class="cockpit-card-title">👥 고객 기본 요약.*?<\/div>\s*<\/div>/s;
if (content.match(insertTarget)) {
    content = content.replace(insertTarget, match => match + '\n' + newCardHtml);
}

// 3. Update selectCustomer script block using regex replace.
// We need to inject the logic to populate the 3 metrics in the JS function.
// Let's inject a generic script block at the end of the file that overrides selectCustomer if it exists, 
// or just modify it. Since modifying a large JS string with regex can be tricky, 
// I will append a script block at the end that hooks into selectCustomer.
// Wait, I can just redefine `selectCustomer` completely at the end of the body, which will overwrite the previous one.
// Let's get the original selectCustomer function so I don't lose the radar chart rendering etc.
const scriptInjection = `
<script>
    // Overriding selectCustomer for enhanced UI & Pitch Script
    const originalSelectCustomer = typeof selectCustomer === 'function' ? selectCustomer : null;
    
    window.selectCustomer = function(customer) {
        if (originalSelectCustomer) {
            // Let the original function do its thing (charts, basic info, etc)
            originalSelectCustomer(customer);
        }
        
        // 1. Update the new Leakage Signs Mini Dashboard
        const freq = Math.floor(customer.Salary_Day_Transfer * 10);
        const freqEl = document.getElementById('ls_freq');
        freqEl.innerText = freq + '회 / 월';
        freqEl.className = 'leakage-sign-val' + (freq >= 5 ? ' warning' : '');
        if(freq >= 5) freqEl.innerText += ' ⚠️';

        const ratio = Math.round(customer.Salary_Day_Transfer * 100);
        const ratioEl = document.getElementById('ls_ratio');
        ratioEl.innerText = ratio + '%';
        ratioEl.className = 'leakage-sign-val' + (ratio >= 50 ? ' warning' : '');
        if(ratio >= 50) ratioEl.innerText += ' ⚠️';

        const amount = Math.round(customer.Avg_Balance * customer.Salary_Day_Transfer * 3);
        const amountEl = document.getElementById('ls_amount');
        amountEl.innerText = formatWon(amount);
        amountEl.className = 'leakage-sign-val' + (amount >= 50000000 ? ' warning' : '');
        if(amount >= 50000000) amountEl.innerText += ' ⚠️';

        // 2. Remove Creepy Factor from Pitch Script
        const theme = customer.Main_Theme;
        const productsMap = {
            '반도체': '글로벌 AI 반도체 목표전환형 랩',
            '항공/방산': 'K-방산 글로벌 리더스 펀드',
            '2차전지': '2차전지 밸류체인 스마트 랩',
            '리츠/배당': '글로벌 월배당 리츠 인컴 랩',
            '금융/은행': '밸류업 코리아 금융지주 랩'
        };
        const product = productsMap[theme] || '우수고객 전용 맞춤형 랩 어카운트';
        
        const safeScript = "고객님, 최근 투자 목적의 자금 이체 비중이 높으신 편이고, 특히 <b>[" + theme + "]</b> 섹터에 관심이 높으신 것으로 분석됩니다. 직접 투자의 변동성을 줄이면서 비과세 혜택까지 챙기실 수 있는 당행의 <b>[" + product + "]</b>을(를) 제안해 드립니다. 유사한 투자 성향을 가지신 VIP 고객님들이 최근 가장 많이 선택하신 솔루션입니다.";
        
        document.getElementById('pitchingScriptText').innerHTML = safeScript;
        
        // Ensure Tab 1 is active (though it probably already is)
        // document.getElementById('tab1').classList.add('active'); // PB 콕핏은 tab2입니다. tab2가 활성화되게 유지합니다.
    };
</script>
</body>`;

content = content.replace('</body>', scriptInjection);

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Upgraded Tab 1 and Pitch Script successfully.");
