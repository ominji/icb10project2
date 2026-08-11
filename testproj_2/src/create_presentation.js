const pptxgen = require("pptxgenjs");
const path = require("path");

function buildPresentation() {
    let pres = new pptxgen();
    pres.layout = 'LAYOUT_16x9'; // 16:9 와이드 슬라이드 레이아웃 지정 (10인치 x 5.625인치)
    pres.author = 'Antigravity AI';
    pres.title = 'iHerb 특가 상품 데이터 EDA 보고서';

    // 스위스 스타일 색상 팔레트 상수 정의
    const BG_COLOR = "FAFAFA";     // Off-white 배경
    const TEXT_BLACK = "111111";   // Near-black 텍스트
    const TEXT_GREY = "555555";    // 보조 회색 텍스트
    const ACCENT_RED = "E8000D";   // 강조 빨간색
    const LINE_GREY = "DDDDDD";    // 구분선 옅은 회색
    const CARD_BG = "FFFFFF";      // 흰색 카드 배경
    const FONT_FACE = "Arial";     // 스위스 스타일의 대표적인 Sans-serif 폰트

    // 스위스 스타일의 고유 공통 요소를 슬라이드에 추가하는 함수
    function applySwissCommonStyle(slide) {
        // 배경색 설정
        slide.background = { color: BG_COLOR };

        // 1. 좌측 가장자리의 시그니처 수직 빨간 바
        slide.addShape(pres.shapes.RECTANGLE, {
            x: 0.1,
            y: 0.1,
            w: 0.08,
            h: 5.425,
            fill: { color: ACCENT_RED },
            line: { style: "none" }
        });
    }

    // ----------------------------------------------------
    // 슬라이드 1: 표지 (Title Slide)
    // ----------------------------------------------------
    let slide1 = pres.addSlide();
    applySwissCommonStyle(slide1);

    // 메인 타이틀
    slide1.addText([
        { text: "iHerb 특가 상품 데이터\n", options: { bold: true, fontSize: 38 } },
        { text: "탐색적 데이터 분석(EDA) 보고서", options: { bold: true, fontSize: 38 } }
    ], {
        x: 0.8,
        y: 1.4,
        w: 8.5,
        h: 1.8,
        fontFace: FONT_FACE,
        color: TEXT_BLACK,
        margin: 0
    });

    // 서브타이틀
    slide1.addText(
        "1,927개 Specials 상품 데이터를 바탕으로 한 플랫폼 판매 및 마케팅 전략 분석",
        {
            x: 0.8,
            y: 3.2,
            w: 8.5,
            h: 0.8,
            fontFace: FONT_FACE,
            fontSize: 15,
            color: TEXT_GREY,
            margin: 0
        }
    );

    // 문서 정보 및 작성자
    slide1.addText([
        { text: "작성일: 2026. 06. 20\n", options: { breakLine: true } },
        { text: "작성자: Antigravity AI Pair" }
    ], {
        x: 0.8,
        y: 4.3,
        w: 5.0,
        h: 0.6,
        fontFace: FONT_FACE,
        fontSize: 11,
        color: "777777",
        margin: 0
    });

    // 데코레이션: 우하단 빨간색 기하학 원
    slide1.addShape(pres.shapes.OVAL, {
        x: 8.0,
        y: 3.6,
        w: 1.3,
        h: 1.3,
        fill: { style: "none" },
        line: { color: ACCENT_RED, width: 2.0 }
    });


    // ----------------------------------------------------
    // 슬라이드 2: 데이터셋 구조 및 개요 (Overview)
    // ----------------------------------------------------
    let slide2 = pres.addSlide();
    applySwissCommonStyle(slide2);

    // 타이틀 및 디바이더 라인
    slide2.addText("01. 데이터셋 구조 및 개요", {
        x: 0.8,
        y: 0.4,
        w: 8.4,
        h: 0.5,
        fontFace: FONT_FACE,
        fontSize: 22,
        bold: true,
        color: TEXT_BLACK,
        margin: 0
    });
    slide2.addShape(pres.shapes.LINE, {
        x: 0.8,
        y: 0.95,
        w: 8.4,
        h: 0,
        line: { color: LINE_GREY, width: 1.0 }
    });

    // 좌측 단: 텍스트 개요 설명
    slide2.addText([
        { text: "데이터셋 구조 및 수집 개요\n\n", options: { bold: true, fontSize: 16, color: TEXT_BLACK } },
        { text: "• 전체 데이터 규모: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "중복이 완전히 배제된 고유 상품 총 1,927개 행 및 71개 열로 구성되어 있습니다.\n\n", options: { breakLine: true } },
        { text: "• 주요 수집 정보: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "상품 ID, 상품 표시명, 브랜드명, 정가, 할인율, 실질 할인가, 평점 및 평점 리뷰 수 정보 등을 정밀 추출하여 수집하였습니다.\n\n", options: { breakLine: true } },
        { text: "• 전처리 정보: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "₩ 기호 및 콤마 단위를 제거해 정가(listPriceValue)를 수치화하고 할인율 파생변수를 추가하여 수치 및 텍스트 통계 기반을 마련했습니다." }
    ], {
        x: 0.8,
        y: 1.3,
        w: 4.2,
        h: 3.8,
        fontFace: FONT_FACE,
        fontSize: 12,
        color: TEXT_GREY,
        margin: 0
    });

    // 우측 단: 3단 정렬된 핵심 KPI 카드
    const kpiData = [
        { label: "총 수집 상품 수", val: "1,927 개", unit: "고유 상품 기준", color: ACCENT_RED },
        { label: "상품 평균 평점", val: "4.6 / 5.0", unit: "소비자 만족도 지표", color: TEXT_BLACK },
        { label: "평균 할인율", val: "26.3 %", unit: "정가 대비 실질 할인 폭", color: TEXT_BLACK }
    ];

    kpiData.forEach((kpi, idx) => {
        let cardY = 1.3 + (idx * 1.2);
        
        // 카드 배경 상자
        slide2.addShape(pres.shapes.RECTANGLE, {
            x: 5.4,
            y: cardY,
            w: 3.8,
            h: 1.0,
            fill: { color: CARD_BG },
            line: { color: LINE_GREY, width: 1.0 }
        });

        // 빨간 포인트 가로 데코선
        slide2.addShape(pres.shapes.RECTANGLE, {
            x: 5.4,
            y: cardY,
            w: 0.06,
            h: 1.0,
            fill: { color: kpi.color },
            line: { style: "none" }
        });

        // 카드 텍스트
        slide2.addText([
            { text: kpi.label + "\n", options: { fontSize: 11, bold: true, color: "777777", breakLine: true } },
            { text: kpi.val + "  ", options: { fontSize: 24, bold: true, color: kpi.color } },
            { text: "(" + kpi.unit + ")", options: { fontSize: 10, color: "888888" } }
        ], {
            x: 5.6,
            y: cardY + 0.1,
            w: 3.5,
            h: 0.8,
            fontFace: FONT_FACE,
            margin: 0
        });
    });


    // ----------------------------------------------------
    // 슬라이드 3: 가격 분석 및 할인 정책 (Price & Discount)
    // ----------------------------------------------------
    let slide3 = pres.addSlide();
    applySwissCommonStyle(slide3);

    // 타이틀 및 디바이더
    slide3.addText("02. 가격 구조 및 할인율 분석", {
        x: 0.8,
        y: 0.4,
        w: 8.4,
        h: 0.5,
        fontFace: FONT_FACE,
        fontSize: 22,
        bold: true,
        color: TEXT_BLACK,
        margin: 0
    });
    slide3.addShape(pres.shapes.LINE, {
        x: 0.8,
        y: 0.95,
        w: 8.4,
        h: 0,
        line: { color: LINE_GREY, width: 1.0 }
    });

    // 좌측 단: 텍스트 서술
    slide3.addText([
        { text: "정가 대비 실질 할인 혜택 비교\n\n", options: { bold: true, fontSize: 16, color: TEXT_BLACK } },
        { text: "• 정가와 할인가 분포: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "평균 정가는 37,624원이며 평균 특가 판매가는 27,501원으로 나타났습니다. 3만 원대 영양제 중심의 특가 구색 배치가 지배적입니다.\n\n", options: { breakLine: true } },
        { text: "• 실질적인 고율 할인: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "평균 할인율은 26.3%로 집계되었습니다. 특히 최대 73%에 이르는 기획 할인도 적용되어 실질적인 혜택 폭이 큽니다.\n\n", options: { breakLine: true } },
        { text: "• 만족도와 가격 관계: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "할인율 크기와 평점 간의 상관관계는 -0.06으로 무관합니다. 이는 상품 할인 폭에 상관없이 우수한 품질이 보장되고 있음을 증명합니다." }
    ], {
        x: 0.8,
        y: 1.3,
        w: 4.2,
        h: 3.8,
        fontFace: FONT_FACE,
        fontSize: 12,
        color: TEXT_GREY,
        margin: 0
    });

    // 우측 단: 차트 이미지 배치
    slide3.addImage({
        path: "testproj_2/images/eda_09_price_vs_discount_price.png",
        x: 5.4,
        y: 1.3,
        w: 3.8,
        h: 3.5
    });


    // ----------------------------------------------------
    // 슬라이드 4: 브랜드 분포 및 마케팅 전략 (Brand Distribution)
    // ----------------------------------------------------
    let slide4 = pres.addSlide();
    applySwissCommonStyle(slide4);

    // 타이틀 및 디바이더
    slide4.addText("03. 브랜드 점유율 및 PB 마케팅", {
        x: 0.8,
        y: 0.4,
        w: 8.4,
        h: 0.5,
        fontFace: FONT_FACE,
        fontSize: 22,
        bold: true,
        color: TEXT_BLACK,
        margin: 0
    });
    slide4.addShape(pres.shapes.LINE, {
        x: 0.8,
        y: 0.95,
        w: 8.4,
        h: 0,
        line: { color: LINE_GREY, width: 1.0 }
    });

    // 좌측 단: 텍스트 서술
    slide4.addText([
        { text: "자사 브랜드(PB)와 글로벌 브랜드 구색 조합\n\n", options: { bold: true, fontSize: 16, color: TEXT_BLACK } },
        { text: "• PB 브랜드 주도형 특가: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "iHerb의 독점 자체 PB 브랜드인 CGN(California Gold Nutrition)이 총 95개 상품으로 특가 등록 1위를 차지해 코너 전반을 주도하고 있습니다.\n\n", options: { breakLine: true } },
        { text: "• 가성비 글로벌 브랜드 안착: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "Nutricost(80개), The Vitamin Shoppe(62개), Swanson(45개) 등 가성비와 유통 파워가 입증된 파트너사 브랜드를 대거 특가 코너에 편입시켰습니다.\n\n", options: { breakLine: true } },
        { text: "• 유통 마진 및 점유 전략: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "마진율 확보가 유리한 CGN을 앵커 상품으로 밀어 이익을 제고하는 한편, 메이저 제조사의 인기 건강기능식품으로 대중 트래픽을 동시 견인하고 있습니다." }
    ], {
        x: 0.8,
        y: 1.3,
        w: 4.2,
        h: 3.8,
        fontFace: FONT_FACE,
        fontSize: 12,
        color: TEXT_GREY,
        margin: 0
    });

    // 우측 단: 차트 이미지 배치
    slide4.addImage({
        path: "testproj_2/images/eda_05_brand_count_bar.png",
        x: 5.4,
        y: 1.3,
        w: 3.8,
        h: 3.5
    });


    // ----------------------------------------------------
    // 슬라이드 5: 상품명 핵심 키워드 분석 (Text Mining)
    // ----------------------------------------------------
    let slide5 = pres.addSlide();
    applySwissCommonStyle(slide5);

    // 타이틀 및 디바이더
    slide5.addText("04. 상품명 핵심 키워드 (TF-IDF)", {
        x: 0.8,
        y: 0.4,
        w: 8.4,
        h: 0.5,
        fontFace: FONT_FACE,
        fontSize: 22,
        bold: true,
        color: TEXT_BLACK,
        margin: 0
    });
    slide5.addShape(pres.shapes.LINE, {
        x: 0.8,
        y: 0.95,
        w: 8.4,
        h: 0,
        line: { color: LINE_GREY, width: 1.0 }
    });

    // 좌측 단: 텍스트 서술
    slide5.addText([
        { text: "텍스트 마이닝을 통한 상품 노출 특성\n\n", options: { bold: true, fontSize: 16, color: TEXT_BLACK } },
        { text: "• 패키지 규격 중심의 노출: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "'캡슐', '60정', '베지', '구미젤리' 등의 제형과 수량 정보 키워드가 TF-IDF 가중치 상위에 분포해 지배적인 영향을 미칩니다.\n\n", options: { breakLine: true } },
        { text: "• 기능성 원료 및 소재: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "'프로바이오틱', '비타민' 등 영양소 원료명 가중치가 크며 'nutrition', 'gold' 등 자사 브랜드 고유명사의 노출 빈도가 높습니다.\n\n", options: { breakLine: true } },
        { text: "• 직구 탐색 최적화: ", options: { bold: true, bullet: true, breakLine: true } },
        { text: "소비자는 성분 함량뿐 아니라 복용 일수(정/캡슐 개수)를 중요하게 탐색하므로 이를 상품명 초입에 정직하고 명확히 표기하는 노출 전략이 확인됩니다." }
    ], {
        x: 0.8,
        y: 1.3,
        w: 4.2,
        h: 3.8,
        fontFace: FONT_FACE,
        fontSize: 12,
        color: TEXT_GREY,
        margin: 0
    });

    // 우측 단: 차트 이미지 배치
    slide5.addImage({
        path: "testproj_2/images/eda_12_text_tfidf_bar.png",
        x: 5.4,
        y: 1.3,
        w: 3.8,
        h: 3.5
    });


    // ----------------------------------------------------
    // 슬라이드 6: 결론 및 비즈니스 제언 (Business Implications)
    // ----------------------------------------------------
    let slide6 = pres.addSlide();
    applySwissCommonStyle(slide6);

    // 타이틀 및 디바이더
    slide6.addText("05. 결론 및 종합 비즈니스 시사점", {
        x: 0.8,
        y: 0.4,
        w: 8.4,
        h: 0.5,
        fontFace: FONT_FACE,
        fontSize: 22,
        bold: true,
        color: TEXT_BLACK,
        margin: 0
    });
    slide6.addShape(pres.shapes.LINE, {
        x: 0.8,
        y: 0.95,
        w: 8.4,
        h: 0,
        line: { color: LINE_GREY, width: 1.0 }
    });

    // 3열 레이아웃을 통해 스위스 디자인 그리드 패턴을 시각적으로 구현
    const finalImplications = [
        {
            num: "01",
            title: "품질과 가격 혜택 연동",
            desc: "평균 평점 4.6점의 매우 신뢰할 수 있는 고만족도 상품들에 평균 26.3%의 높은 가격 할인을 유연하게 부여하고 있습니다. 플랫폼 브랜드 신뢰 훼손 없이 우량 잠재 고객을 집객하는 마케팅 장치 역할을 효과적으로 수행하고 있습니다."
        },
        {
            num: "02",
            title: "PB 제품 앵커링 전략",
            desc: "마진율 통제가 쉬운 자체 브랜드인 California Gold Nutrition(CGN)의 비중을 극대화(특가 상품 1위)하여 수익 구조의 안전판을 다지는 동시에, 다양한 대중적 가성비 수입 브랜드를 적절히 분산 배치하여 구색과 매출을 동시에 확보하고 있습니다."
        },
        {
            num: "03",
            title: "다이내믹 재고 관리 피드",
            desc: "특가 상품 중 품절(isOutOfStock) 상태인 상품이 단 한 건도 노출되지 않은 점은 플랫폼의 다이내믹 재고 필터링이 정상적으로 제어됨을 의미합니다. 유효 재고 위주의 혜택 제공으로 품절 낙담을 방지하고 장바구니 전환율을 끌어올립니다."
        }
    ];

    finalImplications.forEach((imp, idx) => {
        let colX = 0.8 + (idx * 2.9); // 열 배치 좌표 계산 (0.8, 3.7, 6.6)
        
        // 칼럼 카드 배경 상자
        slide6.addShape(pres.shapes.RECTANGLE, {
            x: colX,
            y: 1.4,
            w: 2.6,
            h: 3.4,
            fill: { color: CARD_BG },
            line: { color: LINE_GREY, width: 1.0 }
        });

        // 카드 상단 포인트 빨간색 라벨링 가로 바
        slide6.addShape(pres.shapes.RECTANGLE, {
            x: colX,
            y: 1.4,
            w: 2.6,
            h: 0.08,
            fill: { color: ACCENT_RED },
            line: { style: "none" }
        });

        // 카드 내용 텍스트
        slide6.addText([
            { text: imp.num + "\n", options: { fontSize: 20, bold: true, color: ACCENT_RED, breakLine: true } },
            { text: imp.title + "\n\n", options: { fontSize: 13, bold: true, color: TEXT_BLACK, breakLine: true } },
            { text: imp.desc, options: { fontSize: 11, color: TEXT_GREY } }
        ], {
            x: colX + 0.15,
            y: 1.6,
            w: 2.3,
            h: 3.1,
            fontFace: FONT_FACE,
            margin: 0
        });
    });


    // ----------------------------------------------------
    // 프레젠테이션 파일 디스크 저장
    // ----------------------------------------------------
    const outputDir = path.join("testproj_2", "report");
    const outputPath = path.join(outputDir, "specials_eda_report.pptx");
    
    // 디렉토리가 존재하는지 재차 보장
    const fs = require("fs");
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    pres.writeFile({ fileName: outputPath })
        .then(fileName => {
            console.log("PPTX 생성 성공: " + fileName);
        })
        .catch(err => {
            console.error("PPTX 생성 실패: ", err);
        });
}

buildPresentation();
