const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Fix the font import to the most robust one (Variable font)
content = content.replace(/@import url\('[^']+'\);/, `@import url('https://fastly.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');`);
content = content.replace(/font-family:\s*'Pretendard'[^!]+!important;/, `font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;`);

// 2. Fix the logo. 
// It currently has `<div class="sidebar-logo"> <img ...> </div>`
const newLogo = `
            <div class="sidebar-logo" style="display: flex; align-items: center; gap: 6px;">
                <svg width="36" height="20" viewBox="0 0 45 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M 0 10 L 7 10 L 7 26 L 0 26 Z" fill="#00c896"/>
                    <path d="M 7 10 C 10 2, 22 4, 25 18 C 22 22, 12 26, 7 26 Z" fill="#80e599"/>
                    <path d="M 18 18 C 22 2, 38 0, 45 10 C 40 22, 25 28, 18 26 Z" fill="#00c896"/>
                </svg>
                <span style="font-size: 22px; font-weight: 800; letter-spacing: -1px; color: #111827;">iM뱅크</span>
                <span style="font-size: 13px; color: #6b7280; font-weight: 600; margin-left: 12px; border-left: 1px solid #e5e7eb; padding-left: 12px;">Operation: Money Magnet</span>
            </div>
`;
content = content.replace(/<div class="sidebar-logo">[\s\S]*?<\/div>/, newLogo);

// 3. Fix the GNB tabs styling to match the pill design
const oldGnbTabsCss = `.gnb-tabs .tab-btn {
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
        }`;

const newGnbTabsCss = `.gnb-tabs {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .gnb-tabs .tab-btn {
            border: none;
            background: transparent;
            font-size: 14px;
            font-weight: 700;
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 999px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .gnb-tabs .tab-btn:hover {
            background: #f3f4f6;
        }
        .gnb-tabs .tab-btn.active {
            background: #111827;
            color: #ffffff;
        }`;
content = content.replace(oldGnbTabsCss, newGnbTabsCss);
// Also remove height:100% from .gnb-tabs in CSS
content = content.replace(/height:\s*100%;/g, '');

// Clean up tab button texts to be cleaner (without emojis and brackets if possible, to look like reference)
content = content.replace(/💼 \[영업점 PB용\] 1:1 고객 방어 콕핏/g, 'PB 콕핏');
content = content.replace(/🎯 \[본부 마케팅용\] 타겟 캠페인 허브/g, '마케팅 허브');
content = content.replace(/📊 \[경영진 관제탑\] 전체 자산 방어 통계/g, '경영진 관제탑');

// Clean up the main header to not be redundant since I put it in the logo area
content = content.replace(/<div class="header-title-container">[\s\S]*?<\/div>/, '');

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Fixed font, logo, and tabs exactly to reference.");
