const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Add Pretendard font link
content = content.replace(
    '<link rel="stylesheet" href="https://hangeul.pstatic.net/hangeul_static/css/nanum-square-round.css">',
    '<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />'
);

// 2. Change font-family definitions
content = content.split("'NanumSquareRound'").join("'Pretendard'");

// 3. Replace the logo HTML
const oldLogoHTML = `<div class="sidebar-logo">
                <img src="../im_bank_logo.png" alt="iM뱅크 로고" class="logo-img" onerror="this.src='https://via.placeholder.com/140x30/00bda7/ffffff?text=iM+Bank'">
                <p class="sidebar-subtitle">공식 자산 관리 관제 대시보드</p>
            </div>`;

const newLogoHTML = `<div class="sidebar-logo" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding-bottom: 15px; border-bottom: 1px dashed rgba(0, 0, 0, 0.08);">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 6px;">
                    <!-- iM뱅크 로고 심볼 SVG -->
                    <svg width="45" height="26" viewBox="0 0 45 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M 0 10 L 7 10 L 7 26 L 0 26 Z" fill="#00c896"/>
                        <path d="M 7 10 C 10 2, 22 4, 25 18 C 22 22, 12 26, 7 26 Z" fill="#80e599"/>
                        <path d="M 18 18 C 22 2, 38 0, 45 10 C 40 22, 25 28, 18 26 Z" fill="#00c896"/>
                    </svg>
                    <!-- iM뱅크 텍스트 -->
                    <span style="font-size: 26px; font-weight: 800; letter-spacing: -1.5px; color: #111827; margin-top: 2px;">iM 뱅크</span>
                </div>
                <p class="sidebar-subtitle">공식 자산 관리 관제 대시보드</p>
            </div>`;

content = content.replace(oldLogoHTML, newLogoHTML);

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Font and Logo updated successfully!");
