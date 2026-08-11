import os
import sys

def convert_pptx_to_pdf():
    # 경로 설정 (절대경로 확보 필요)
    base_dir = os.path.abspath(os.getcwd())
    pptx_path = os.path.join(base_dir, "testproj_2", "report", "specials_eda_report.pptx")
    pdf_path = os.path.join(base_dir, "testproj_2", "report", "specials_eda_report.pdf")

    print(f"변환 대상 PPTX: {pptx_path}")
    print(f"변환 결과 PDF: {pdf_path}")

    # 파일 존재 여부 확인
    if not os.path.exists(pptx_path):
        print("오류: PPTX 파일이 존재하지 않습니다.")
        return

    # 윈도우 win32com 모듈 로드
    try:
        import win32com.client
    except ImportError:
        print("오류: pywin32 패키지가 설치되지 않았거나 로드할 수 없습니다.")
        return

    powerpoint = None
    presentation = None

    try:
        # PowerPoint 애플리케이션 시작
        print("PowerPoint COM 객체 기동 중...")
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        # PPTX 파일 열기 (WithWindow=False 옵션으로 창 노출 없이 백그라운드 기동)
        print("PPTX 파일 로드 중...")
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
        
        # PDF로 저장 (Format 32: ppSaveAsPDF)
        print("PDF로 변환 및 저장 중...")
        presentation.SaveAs(pdf_path, 32)
        print("PDF 변환 완료!")
        
    except Exception as e:
        print(f"변환 작업 중 오류 발생: {e}")
        
    finally:
        # 리소스 해제 및 기동된 PowerPoint 종료
        try:
            if presentation:
                presentation.Close()
                print("프레젠테이션 객체 닫기 완료.")
        except Exception:
            pass
            
        try:
            if powerpoint:
                powerpoint.Quit()
                print("PowerPoint 프로세스 종료 완료.")
        except Exception:
            pass

if __name__ == "__main__":
    convert_pptx_to_pdf()
