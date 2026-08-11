import os
import re
import asyncio
from markdown_it import MarkdownIt
from playwright.async_api import async_playwright

async def convert_md_to_pdf(md_path, pdf_path):
    # 1. 마크다운 파일 읽기
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    # 2. 마크다운 -> HTML 변환 (markdown-it 사용)
    md = MarkdownIt()
    html_body = md.render(md_text)
    
    # 3. 이미지 상대 경로를 절대 경로로 변환하여 브라우저에서 로드 가능하게 함
    # markdown-it 렌더링 결과 이미지 태그: <img src="../images/..." alt="..." />
    # 프로젝트 루트 및 파일 디렉토리 절대경로 획득
    md_dir = os.path.dirname(os.path.abspath(md_path))
    project_root = os.path.abspath(os.path.join(md_dir, "..")) # card/
    
    def replace_img_src(match):
        src = match.group(1)
        # 상대 경로 계산
        if src.startswith("../images"):
            abs_src = os.path.abspath(os.path.join(md_dir, src))
        elif src.startswith("images"):
            abs_src = os.path.abspath(os.path.join(project_root, src))
        else:
            abs_src = os.path.abspath(os.path.join(md_dir, src))
            
        # 파일 URL 형식으로 변경 (Windows 백슬래시 처리)
        file_url = "file:///" + abs_src.replace("\\", "/")
        return f'src="{file_url}"'
        
    html_body = re.sub(r'src="([^"]+)"', replace_img_src, html_body)
    
    # 4. 고급스러운 인쇄용 CSS 입히기
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    body {
        font-family: 'Noto Sans KR', sans-serif;
        line-height: 1.6;
        color: #333;
        padding: 40px;
        max-width: 900px;
        margin: 0 auto;
        font-size: 14px;
    }
    h1 {
        font-size: 28px;
        border-bottom: 2px solid #2ca02c;
        padding-bottom: 10px;
        color: #111;
        margin-top: 40px;
    }
    h2 {
        font-size: 20px;
        border-bottom: 1px solid #ddd;
        padding-bottom: 8px;
        color: #222;
        margin-top: 30px;
        page-break-after: avoid;
    }
    h3 {
        font-size: 16px;
        color: #333;
        margin-top: 20px;
        page-break-after: avoid;
    }
    p {
        margin-bottom: 15px;
        text-align: justify;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 13px;
        page-break-inside: avoid;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #f5f5f5;
        font-weight: 500;
    }
    blockquote {
        margin: 20px 0;
        padding: 15px 20px;
        background-color: #f9f9f9;
        border-left: 5px solid #2ca02c;
        color: #555;
        page-break-inside: avoid;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 20px auto;
        border: 1px solid #eee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        page-break-inside: avoid;
    }
    hr {
        border: 0;
        height: 1px;
        background: #ddd;
        margin: 40px 0;
    }
    /* 인쇄 전용 페이지 구분 및 여백 제어 */
    @page {
        size: A4;
        margin: 20mm;
    }
    pre, code {
        font-family: monospace;
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 12px;
    }
    """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{css}</style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    # 5. 임시 HTML 파일 쓰기
    temp_html_path = md_path.replace(".md", "_temp.html")
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"HTML 템플릿 생성 완료: {temp_html_path}")
    
    # 6. Playwright로 PDF 인쇄
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # 로컬 html 파일 로드
        abs_html_path = "file:///" + os.path.abspath(temp_html_path).replace("\\", "/")
        await page.goto(abs_html_path, wait_until="networkidle")
        
        # PDF 출력 옵션 설정
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}
        )
        await browser.close()
        
    # 임시 파일 제거
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)
        
    print(f"PDF 변환 완료: {pdf_path}")

async def main():
    reports = [
        ("card/report/card_eda_report.md", "card/report/card_eda_report_v2.pdf"),
        ("card/report/card_eda_report_2025.md", "card/report/card_eda_report_2025_v2.pdf")
    ]
    
    for md, pdf in reports:
        if os.path.exists(md):
            print(f"변환 작업 시작: {md} -> {pdf}")
            await convert_md_to_pdf(md, pdf)
        else:
            print(f"파일을 찾을 수 없습니다: {md}")

if __name__ == "__main__":
    asyncio.run(main())
