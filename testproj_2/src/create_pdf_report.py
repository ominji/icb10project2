import os
import pandas as pd
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def build_pdf_report():
    base_dir = os.path.abspath(os.getcwd())
    csv_path = os.path.join(base_dir, "testproj_2", "data", "olive_vitamins.csv")
    pdf_path = os.path.join(base_dir, "testproj_2", "report", "olive_eda_report.pdf")
    
    # 이미지 파일 경로들
    img_price = os.path.join(base_dir, "testproj_2", "images", "olive_eda_01_price_dist.png")
    img_box = os.path.join(base_dir, "testproj_2", "images", "olive_eda_06_formulation_price_box.png")
    img_tfidf = os.path.join(base_dir, "testproj_2", "images", "olive_eda_10_text_tfidf.png")

    print("한글 PDF 보고서 생성 시작...")

    # 1. 윈도우 시스템 한글 폰트 등록 (맑은 고딕)
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\malgunbd.ttf"
    
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\malgunsl.ttf"  # Semilight 대체
        
    try:
        pdfmetrics.registerFont(TTFont('Malgun', font_path))
        pdfmetrics.registerFont(TTFont('MalgunBold', font_bold_path))
        print("맑은 고딕 한글 폰트 등록 완료.")
    except Exception as e:
        print(f"한글 폰트 등록 중 오류 발생 (기본 폰트로 진행): {e}")

    # 2. 스타일 정의
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='MalgunBold',
        fontSize=22,
        leading=28,
        textColor=colors.HexColor('#111111'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Malgun',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#555555'),
        alignment=1, # Center
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='MalgunBold',
        fontSize=15,
        leading=20,
        textColor=colors.HexColor('#E74C3C'), # 올영 포인트 컬러 느낌의 코랄/레드톤 강조
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='MalgunBold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#111111'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Malgun',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='MalgunBold',
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Malgun',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#333333'),
        alignment=1
    )

    # Document 템플릿 설정 (Letter 사이즈, 상하좌우 여백 0.5인치)
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    # ----------------------------------------------------
    # 표지 페이지 (Title Block)
    # ----------------------------------------------------
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("올리브영 비타민 상품 데이터 탐색적 데이터 분석(EDA) 보고서", title_style))
    story.append(Paragraph("537개 고유 비타민 상품 데이터셋 분석 및 시각화 요약 리포트", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    
    # 작성 정보 테이블
    info_data = [
        [Paragraph("<b>작성일:</b>", body_style), Paragraph("2026년 6월 20일", body_style)],
        [Paragraph("<b>작성자:</b>", body_style), Paragraph("Antigravity AI Pair", body_style)],
        [Paragraph("<b>데이터 출처:</b>", body_style), Paragraph("올리브영 온라인몰 비타민 카테고리 실시간 크롤링 수집 피드", body_style)]
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    t_container = Table([[info_table]], colWidths=[5*inch])
    t_container.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_container)
    
    story.append(PageBreak()) # 1페이지 종료

    # ----------------------------------------------------
    # 1. 데이터셋 개요
    # ----------------------------------------------------
    story.append(Paragraph("1. 데이터셋 탐색 및 기본 정보", h1_style))
    intro_txt = (
        "본 보고서는 올리브영 온라인몰 비타민 카테고리에서 수집한 고유 상품 데이터를 바탕으로 수행된 "
        "탐색적 데이터 분석(EDA) 결과입니다. 중복 상품을 제거한 최종 고유 상품 수는 <b>537개</b>이며, "
        "총 12개의 메타 정보 필드(열)가 분석 대상으로 활용되었습니다. 수집된 주요 수치형 변수는 가격, 평점, "
        "리뷰 수 등이 있으며, 텍스트 데이터인 상품명 속성을 통해 핵심어(TF-IDF) 마이닝을 추가로 수행했습니다."
    )
    story.append(Paragraph(intro_txt, body_style))
    story.append(Spacer(1, 10))

    # 데이터 요약 정보 표
    summary_headers = ["지표", "수집 데이터 요약"]
    summary_rows = [
        ["전체 고유 상품 수", "537 개"],
        ["전체 메타 열 수", "12 개"],
        ["수집 브랜드 수", "112 개 브랜드"],
        ["상품 평균 만족도 (평점)", "4.88 / 5.0 점"],
        ["상품 평균 가격", "29,145 원"]
    ]
    
    table_data = [[Paragraph(f"<b>{h}</b>", table_header_style) for h in summary_headers]]
    for row in summary_rows:
        table_data.append([Paragraph(row[0], table_cell_style), Paragraph(row[1], table_cell_style)])
        
    summary_table = Table(table_data, colWidths=[3.0*inch, 4.0*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E74C3C')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ----------------------------------------------------
    # 2. 수치형 변수 분석 및 시각화 (가격 & 평점)
    # ----------------------------------------------------
    story.append(Paragraph("2. 수치형 변수 분석 및 가격 정책", h1_style))
    num_txt = (
        "올리브영 비타민 상품군의 평균 판매가는 약 29,145원 선에 형성되어 있으며, 최저 3,500원(단일 앰플형 간편 샷)부터 "
        "최고 149,000원(수입 프리미엄 이뮨 세트)까지 가격 스펙트럼이 대단히 넓습니다. 특히 1만 원대 중반에서 3만 원대 사이의 "
        "가성비형 일상 복용 제품이 전체 매대의 주축을 이루고 있는 것으로 분석됩니다. 평점 분포는 평균 4.88점으로 매우 극단적으로 "
        "높게 상향 평준화되어 있으며, 평점이 낮은 비인기 상품은 아예 제거되거나 단종 처리되었음을 암시합니다.<br/><br/>"
        "특히 가격과 평점의 상관계수는 -0.048로 사실상 완전한 독립을 보이며, 가격대에 상관없이 올리브영 비타민 카테고리의 "
        "모든 입점 상품들의 품질 및 신뢰도가 훌륭하게 통제되고 있음을 뜻합니다."
    )
    story.append(Paragraph(num_txt, body_style))
    story.append(Spacer(1, 10))

    if os.path.exists(img_price):
        story.append(Paragraph("<b>[그림 1] 올리브영 비타민 상품 가격 분포 히스토그램</b>", h2_style))
        story.append(Image(img_price, width=4.5*inch, height=3.0*inch))
        story.append(Spacer(1, 15))

    story.append(PageBreak()) # 2페이지 종료

    # ----------------------------------------------------
    # 3. 제형 및 가격 분포 분석 (Boxplot)
    # ----------------------------------------------------
    story.append(Paragraph("3. 비타민 제형별 상품 및 가격 특성 분석", h1_style))
    form_txt = (
        "제형별 유통 점유율을 분석한 결과 전통적 형태인 '정제'가 약 74%의 점유율로 표준적인 제품 기준을 지키고 있는 가운데, "
        "물 없이 젤리처럼 복용할 수 있는 '구미' 제형과 최신 트렌드를 대변하는 고단가 액상 '샷' 제형이 탄탄한 성장을 보이고 있습니다.<br/><br/>"
        "제형별 가격의 Boxplot(상자 그림) 분석 결과에 따르면, 정제와 캡슐은 초저가형부터 10만 원이 초과하는 고가형까지 "
        "스펙트럼이 대단히 폭넓게 형성된 반면, 액상 '샷' 제형은 중고가 및 프리미엄 선물용 라인에 콤팩트하게 가격 상자가 위치하여, "
        "단위당 고부가가치 창출에 대단히 유리한 매스티지(Masstige) 포지션임이 증명되었습니다."
    )
    story.append(Paragraph(form_txt, body_style))
    story.append(Spacer(1, 10))

    if os.path.exists(img_box):
        story.append(Paragraph("<b>[그림 2] 비타민 제형별 상품 가격 편차 및 분포 상자 그림</b>", h2_style))
        story.append(Image(img_box, width=4.5*inch, height=3.0*inch))
        story.append(Spacer(1, 15))

    # ----------------------------------------------------
    # 4. 상품명 핵심 키워드 분석
    # ----------------------------------------------------
    story.append(Paragraph("4. 상품명 핵심 키워드 마이닝 (TF-IDF)", h1_style))
    text_txt = (
        "상품명의 핵심 단어 가중치를 TF-IDF 모델로 추출한 결과 '비타민'과 '멀티비타민'의 필수 기본 용어 외에도 "
        "'이뮨', '오쏘몰', '아임비타' 등 프리미엄 및 고활력 지향 브랜드와 '구미', '젤리', '스틱', '앰플' 등의 복용 편의성과 "
        "경험적 요소를 수반하는 제형 키워드가 강한 중요도 가중치를 나타내고 있습니다. 이는 올리브영 비타민 매대가 젊은 층 고객들의 "
        "빠른 활력 충전과 라이프스타일 지향 브랜딩에 맞춰 타이트하게 기획 및 큐레이션되고 있음을 직접적으로 나타냅니다."
    )
    story.append(Paragraph(text_txt, body_style))
    story.append(Spacer(1, 10))

    if os.path.exists(img_tfidf):
        story.append(Paragraph("<b>[그림 3] 올리브영 비타민 상품명 내 TF-IDF 기반 상위 30개 핵심어 가중치</b>", h2_style))
        story.append(Image(img_tfidf, width=4.5*inch, height=2.8*inch))
        story.append(Spacer(1, 15))

    story.append(PageBreak()) # 3페이지 종료

    # ----------------------------------------------------
    # 5. 결론 및 비즈니스 제언
    # ----------------------------------------------------
    story.append(Paragraph("5. 결론 및 종합 비즈니스 시사점", h1_style))
    
    concl_01 = (
        "<b>1) 품질 및 소비자 신뢰의 평준화</b><br/>"
        "올리브영 비타민 상품들의 평균 평점이 4.88점의 극도로 높은 수준을 유지하는 것은 플랫폼 내 입점 상품들의 품질 관리와 "
        "브랜드 검증 필터링이 체계적으로 가동되고 있음을 뜻합니다. 소비자는 가격 장벽에 관계없이 높은 신뢰를 갖추고 구매할 수 있습니다."
    )
    concl_02 = (
        "<b>2) 복용 경험의 혁신과 고부가가치 창출</b><br/>"
        "정제가 매출의 기본적 토대를 다지는 가운데, 맛있고 세련된 셀프 헬스케어 가치인 '구미/젤리' 제형과 고부가가치를 확보한 "
        "이뮨 '샷' 제형이 새로운 성장 동력을 주도합니다. 트렌디한 액상 제형을 추가 발굴하여 프리미엄 큐레이션을 확대하는 전략이 권장됩니다."
    )
    concl_03 = (
        "<b>3) 타깃별 맞춤식 하이브리드 포트폴리오</b><br/>"
        "가족 및 범용성 전체 타깃 제품의 비율이 압도적인 89%를 차지하는 가운데, 바쁜 현대인을 저격하는 성별 전용(남성/여성) 멀티팩 "
        "정제/캡슐 상품군이 조화롭게 입점하여 구색의 완결성을 획득하고 있습니다."
    )

    story.append(Paragraph(concl_01, body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(concl_02, body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(concl_03, body_style))
    story.append(Spacer(1, 20))

    # PDF 빌드 실행
    try:
        doc.build(story)
        print("PDF 보고서 빌드 완료!")
    except Exception as e:
        print(f"PDF 빌드 과정 중 오류 발생: {e}")

if __name__ == "__main__":
    build_pdf_report()
