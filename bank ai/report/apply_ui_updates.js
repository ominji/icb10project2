const fs = require('fs');

const filePath = 'money_magnet_dashboard.html';
let content = fs.readFileSync(filePath, 'utf-8');

// 1. CSS Updates
const cssAdd = `
        .cockpit-row-1 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }
        .leakage-signs-card { display: flex; flex-direction: column; gap: 12px; height:100%; justify-content:center;}
        .leakage-sign-item { background: var(--bg-dark); padding: 12px 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.05); }
        .leakage-sign-title { font-size: 13px; color: var(--text-muted); font-weight: 600; }
        .leakage-sign-val { font-size: 15px; font-weight: 800; color: var(--text-main); }
        .leakage-sign-val.warning { color: var(--accent-red); }
`;
content = content.replace('</style>', cssAdd + '</style>');

// 2. Tabs Update
const oldTabs = `            <div class="tabs-container">
                <div class="tab active" onclick="switchTab('tab1', this)">[ 📊 경영진 관제탑 ] 실시간 마그넷 현황</div>
                <div class="tab" onclick="switchTab('tab2', this)">[ 🎯 타겟 캠페인 허브 ] 자산 유출 방어 리스트</div>
            </div>`;
const newTabs = `            <div class="tabs-container">
                <div class="tab active" onclick="switchTab('tab1', this)">[ 💼 영업점 PB용 ] 1:1 고객 방어 콕핏</div>
                <div class="tab" onclick="switchTab('tab2', this)">[ 🎯 본부 마케팅용 ] 타겟 캠페인 허브</div>
                <div class="tab" onclick="switchTab('tab3', this)">[ 📊 경영진 관제탑 ] 전체 자산 방어 통계</div>
            </div>`;
content = content.replace(oldTabs, newTabs);

// 3. Rename Tab Sections
content = content.replace('<section class="tab-pane active" id="tab1">', '<section class="tab-pane" id="tab3">');
content = content.replace('<section class="tab-pane" id="tab2">', '<section class="tab-pane active" id="tab1">');

// 4. Insert Tab 2 content
const tab2Html = `
            <!-- ------------------ 탭 2: 본부 마케팅용 ------------------ -->
            <section class="tab-pane" id="tab2">
                <div style="padding:60px 20px; text-align:center; color:#94a3b8;">
                    <div style="font-size:40px; margin-bottom:20px;">🎯</div>
                    <h2 style="color:var(--primary); margin-bottom:10px;">타겟 캠페인 허브</h2>
                    <p>본부 마케팅 캠페인 기획 및 성과 분석 화면입니다.<br>(추후 CRM 데이터 연동 예정)</p>
                </div>
            </section>
`;
content = content.replace('<section class="tab-pane" id="tab3">', tab2Html + '\n            <section class="tab-pane" id="tab3">');

// 5. PB Cockpit row-1 replacement
const row1Regex = /<div class="cockpit-row-1">[\s\S]*?<\/div>\s*<\/div>\s*<!-- 2단계/;
const newRow1 = `<div class="cockpit-row-1">
                            <!-- 인적 요약 정보 -->
                            <div class="cockpit-card">
                                <div class="cockpit-card-title">👥 고객 기본 요약 <span style="font-size:16px;">👤</span></div>
                                <div class="cockpit-info-list" id="custBasicInfo">
                                    <!-- 동적 렌더링 -->
                                </div>
                            </div>
                            <!-- 이탈 징후 분석 -->
                            <div class="cockpit-card">
                                <div class="cockpit-card-title">📉 이탈 징후 집중 분석 <span style="font-size:16px;">⚠️</span></div>
                                <div class="leakage-signs-card">
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">월 평균 타행 이체 빈도</span>
                                        <span class="leakage-sign-val" id="ls_freq">0회</span>
                                    </div>
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">급여 대비 이체 비율</span>
                                        <span class="leakage-sign-val" id="ls_ratio">0%</span>
                                    </div>
                                    <div class="leakage-sign-item">
                                        <span class="leakage-sign-title">최근 3개월 누적 이체 금액</span>
                                        <span class="leakage-sign-val" id="ls_amount">₩0</span>
                                    </div>
                                </div>
                            </div>
                            <!-- 마이데이터 X-Ray -->
                            <div class="cockpit-card">
                                <div class="cockpit-card-title">🔍 마이데이터 외부 자산 X-Ray <span style="font-size:16px;">📊</span></div>
                                <div class="cockpit-chart-wrapper" style="position:relative;">
                                    <canvas id="custXrayDoughnut"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- 2단계`;
content = content.replace(row1Regex, newRow1);

// 6. Buttons replacement
const buttonRegex = /<button class="btn-large" id="defendBtn" onclick="runDefendMagnet\(\)">🚀 마그넷 솔루션 가동 \(방어 실행\)<\/button>/;
const newButtons = `<div style="display:flex; gap:10px; width:100%;">
                                            <button class="btn-large" id="defendBtn" onclick="runDefendMagnet()" style="flex:1;">🚀 마그넷 솔루션 (방어 실행)</button>
                                            <button class="btn-large" id="rolloverBtn" onclick="runRollover()" style="flex:1; background-color:#3b82f6; color:#fff;">🔄 Rollover (자산 이전) 제안</button>
                                        </div>`;
content = content.replace(buttonRegex, newButtons);

// 7. Add X-Ray chart variable
content = content.replace('let radarChartInstance = null;', 'let radarChartInstance = null;\n        let xrayChartInstance = null;');

// 8. Override selectCustomer JS Logic
const scriptAppend = `
    <script>
        const _originalSelectCustomer = selectCustomer;
        window.selectCustomer = function(customer) {
            _originalSelectCustomer(customer);
            
            // 1. 이탈 징후 미니 대시보드 업데이트
            const freq = Math.floor(customer.Salary_Day_Transfer * 10);
            const freqEl = document.getElementById('ls_freq');
            if(freqEl) {
                freqEl.innerText = freq + '회 / 월';
                freqEl.className = 'leakage-sign-val' + (freq >= 4 ? ' warning' : '');
                if(freq >= 4) freqEl.innerHTML += ' <span style="font-size:12px;">⚠️</span>';
            }

            const ratio = Math.round(customer.Salary_Day_Transfer * 100);
            const ratioEl = document.getElementById('ls_ratio');
            if(ratioEl) {
                ratioEl.innerText = ratio + '%';
                ratioEl.className = 'leakage-sign-val' + (ratio >= 40 ? ' warning' : '');
                if(ratio >= 40) ratioEl.innerHTML += ' <span style="font-size:12px;">⚠️</span>';
            }

            const amount = Math.round(customer.Avg_Balance * customer.Salary_Day_Transfer * 3);
            const amountEl = document.getElementById('ls_amount');
            if(amountEl) {
                amountEl.innerText = formatWon(amount);
                amountEl.className = 'leakage-sign-val' + (amount >= 50000000 ? ' warning' : '');
                if(amount >= 50000000) amountEl.innerHTML += ' <span style="font-size:12px;">⚠️</span>';
            }

            // 2. 마이데이터 X-Ray 도넛 차트 렌더링 (스마트 블러링 적용)
            const ctxXray = document.getElementById('custXrayDoughnut');
            if (ctxXray) {
                if (xrayChartInstance) xrayChartInstance.destroy();
                
                // 자산군 라벨링 매핑 (크리피 팩터 제거)
                const assetMap = {
                    '반도체': '해외 테크/성장주',
                    '2차전지': '미래 산업 혁신주',
                    '항공/방산': '가치주/인프라',
                    '리츠/배당': '국내 고배당주/부동산',
                    '금융/은행': '금융/안전자산'
                };
                
                // 원본 테마 점수 기반 가상 비중 계산
                const rawValues = [customer['반도체'], customer['2차전지'], customer['항공/방산'], customer['리츠/배당'], customer['금융/은행']];
                const sum = rawValues.reduce((a, b) => a + b, 0);
                // 10%는 무조건 투자 대기 현금으로 설정
                const investCash = 10;
                let dataVals = rawValues.map(v => Math.round((v / sum) * 90));
                
                // 만약 합이 안맞으면 보정
                const currentSum = dataVals.reduce((a,b)=>a+b, 0);
                if (currentSum !== 90) dataVals[0] += (90 - currentSum);

                xrayChartInstance = new Chart(ctxXray.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: [assetMap['반도체'], assetMap['2차전지'], assetMap['항공/방산'], assetMap['리츠/배당'], assetMap['금융/은행'], '투자 대기 현금'],
                        datasets: [{
                            data: [...dataVals, investCash],
                            backgroundColor: ['#00bda7', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#64748b'],
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return ' ' + context.label + ': ' + context.parsed + '%';
                                    }
                                }
                            }
                        }
                    }
                });
            }

            // 3. PB 포트폴리오 리밸런싱 힌트 (AI 피칭 스크립트 수정)
            const theme = customer.Main_Theme;
            const assetName = assetMap[theme] || '특정 주식';
            const wrapProducts = {
                '반도체': 'iM 글로벌 AI 반도체 목표전환형 랩',
                '2차전지': 'K-배터리 밸류체인 스마트 랩',
                '항공/방산': 'iM 방산 테마 글로벌 랩',
                '리츠/배당': 'iM 글로벌 부동산 리츠 인컴 랩',
                '금융/은행': '금융 밸류업 고배당 신탁'
            };
            const recProduct = wrapProducts[theme] || '우수고객 전용 맞춤형 랩';

            const card = document.getElementById('playbookCardContent');
            if(card) {
                const taxSaving = Math.round((customer.Avg_Balance * customer.Salary_Day_Transfer * 0.075 * 0.154)).toLocaleString();
                card.innerHTML = \`
                    <h5 class="playbook-header-title">💡 단디 AI 집중 분석 및 제언</h5>
                    <div class="script-box">
                        🗣 <b>AI 피칭 가이드:</b><br>
                        "고객님, 최근 마이데이터 분석 결과 타 증권사로 자금 이체가 꾸준히 발생하고 있으며, 특히 <b>[\${assetName}]</b> 비중이 높으신 것으로 분석됩니다.<br>
                        개별 주식 직접 투자의 변동성 위험을 감내하시기보다, 우수 VIP 고객님들이 최근 가장 많이 롤오버하시는 당행의 <b>[\${recProduct}]</b>을(를) 제안해 드립니다. 이를 통해 연간 약 ₩<span class="tax-saving-text-placeholder">\${taxSaving}</span>의 세금 이연 효과도 함께 누리실 수 있습니다."
                    </div>
                    <div style="margin-top: 5px;">
                        <span style="font-size:11px; color:#94a3b8; font-weight:600; display:block; margin-bottom:4px;">🧲 매칭된 당행 랩/신탁 상품:</span>
                        <div class="product-chips-container">
                            <span class="product-chip">\${recProduct}</span>
                        </div>
                    </div>
                \`;
            }
        };

        window.runRollover = function() {
            const c = state.selectedCustomer;
            if (!c) return;
            showToast('🔄 Rollover 제안 완료! 고객 CRM에 제안 이력이 등록되었습니다.');
        };

        // runDefendMagnet Override for visual effect
        const _origRunDefend = runDefendMagnet;
        window.runDefendMagnet = function() {
            const c = state.selectedCustomer;
            if (!c) return;
            
            // 기존 방어 로직 실행
            _origRunDefend();
            
            // 시각적 효과: 누수율을 0%로 애니메이션
            const ratioEl = document.getElementById('ls_ratio');
            if(ratioEl) {
                ratioEl.innerText = '0%';
                ratioEl.className = 'leakage-sign-val'; // remove warning
                ratioEl.style.color = '#34d399'; // green success
                ratioEl.innerHTML += ' <span style="font-size:12px;">✅</span>';
            }
            const freqEl = document.getElementById('ls_freq');
            if(freqEl) {
                freqEl.innerText = '0회 / 월';
                freqEl.className = 'leakage-sign-val';
            }
            const amountEl = document.getElementById('ls_amount');
            if(amountEl) {
                amountEl.innerText = '₩0';
                amountEl.className = 'leakage-sign-val';
            }
            
            // 탭3 데이터도 살짝 업데이트해줌 (시각적 피드백)
            const kpi3Val = document.getElementById('kpi3_val');
            if(kpi3Val) {
                let currentVal = parseInt(kpi3Val.innerText.replace(/,/g, ''));
                if(isNaN(currentVal)) currentVal = 0;
                kpi3Val.innerText = (currentVal + 1).toLocaleString() + '건';
            }
            
            showToast(\`🧲 방어 성공! \${c.Name} 고객님의 자산이 iM뱅크 내로 Lock-in 되었습니다.\`);
        };
    </script>
</body>
`;
content = content.replace('</body>', scriptAppend);

fs.writeFileSync(filePath, content, 'utf-8');
console.log("UI updates applied successfully via Node.js script.");
