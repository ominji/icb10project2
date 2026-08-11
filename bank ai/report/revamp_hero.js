const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// Replace the current main-header with a SaaS Hero section matching the screenshot
const oldHeaderRegex = /<header class="main-header">[\s\S]*?<\/button>\s*<div id="filterPanel" class="filter-panel">/;

const newHeader = `
        <div style="padding: 40px 0 40px; text-align: left; position: relative;">
            <div style="display: inline-block; background: #e2f1f0; color: #00c896; padding: 6px 14px; border-radius: 999px; font-size: 13px; font-weight: 700; margin-bottom: 20px;">iM Bank · PB Cockpit</div>
            <h1 style="font-size: 42px; font-weight: 800; color: #111827; letter-spacing: -1.5px; margin-bottom: 20px; line-height: 1.3;">이탈 위기의 고객 자산을 한눈에,<br>방어 전략은 한 줄로.</h1>
            <p style="font-size: 16px; color: #6b7280; margin-bottom: 32px; font-weight: 500;">iM뱅크 우수 고객의 머니무브(자산 이탈) 징후를 실시간으로 탐지하고 선제적으로 방어합니다.<br>스마트 타겟팅을 통해 빠르게 위험 고객을 찾아 조치해 보세요.</p>
            
            <div style="display: flex; gap: 16px; align-items: center; position: relative;">
                <button class="filter-toggle-btn" style="background: #00c896; color: white; border: none; padding: 12px 24px; font-size: 15px; border-radius: 8px; font-weight: 700;" onclick="document.getElementById('filterPanel').classList.toggle('show')">
                    스마트 타겟팅 (고급 필터) 시작
                </button>
                <div style="font-size: 13px; color: #9ca3af; font-weight: 600; margin-left: 8px;">● 데이터 기준 시점 — <span id="currentDateSpan">2026-06-10</span></div>
                
                <!-- Filter Panel moves here, position adjusted -->
                <div id="filterPanel" class="filter-panel" style="top: 100%; left: 0; right: auto; margin-top: 16px;">
`;

if (content.match(oldHeaderRegex)) {
    content = content.replace(oldHeaderRegex, newHeader);
}

// Clean up the top text that was floating around
content = content.replace(/<div style="font-size: 14px; color: var\(--text-muted\); margin-bottom: 20px; font-weight: 500;">[\s\S]*?<\/div>/, '');

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Hero section revamped to match screenshot perfectly.");
