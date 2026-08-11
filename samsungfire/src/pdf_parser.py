import os
import requests
from pypdf import PdfReader
import json
from typing import List, Dict

PDF_URL = "https://www.samsungfire.com/publication/pdf/20071_0_20250816_file1.pdf"
PDF_SAVE_PATH = os.path.join("samsungfire", "data", "20071_0_20250816_file1.pdf")
CHUNKS_SAVE_PATH = os.path.join("samsungfire", "data", "chunks.json")

def download_pdf(url: str = PDF_URL, save_path: str = PDF_SAVE_PATH) -> str:
    """삼성화재 약관 PDF 문서를 다운로드합니다."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        print(f"[INFO] 이미 PDF 파일이 존재합니다: {save_path}")
        return save_path

    print(f"[INFO] PDF 다운로드 중: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"[INFO] PDF 다운로드 완료: {save_path} ({os.path.getsize(save_path)} bytes)")
    return save_path

def extract_text_from_pdf(pdf_path: str = PDF_SAVE_PATH) -> List[Dict[str, any]]:
    """PDF에서 페이지별 텍스트를 추출합니다."""
    reader = PdfReader(pdf_path)
    pages_data = []
    
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # 텍스트 전처리 (공백 및 연속 줄바꿈 정리)
        text = text.strip()
        if text:
            pages_data.append({
                "page": idx + 1,
                "content": text
            })
            
    print(f"[INFO] 총 {len(reader.pages)}페이지 중 {len(pages_data)}페이지 텍스트 추출 완료")
    return pages_data

def chunk_text(pages_data: List[Dict[str, any]], chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, any]]:
    """페이지별 텍스트를 중첩(overlap)을 둔 문단/문장 단위 청크로 분할합니다."""
    chunks = []
    chunk_id = 0

    for item in pages_data:
        page_num = item["page"]
        text = item["content"]
        
        # 텍스트를 적당한 길이로 분할
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_content = text[start:end]
            
            # 끝 지점이 단어 중간이 되지 않도록 공백이나 줄바꿈 위치 조정
            if end < text_len and " " in text[end-20:end]:
                last_space = text.rfind(" ", start, end)
                if last_space > start + (chunk_size // 2):
                    end = last_space
                    chunk_content = text[start:end]

            chunk_content = chunk_content.strip()
            if len(chunk_content) > 20:  # 의미 없는 너무 짧은 청크 제외
                chunk_id += 1
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": page_num,
                    "content": chunk_content
                })
            
            start = end - overlap if end - overlap > start else end

    print(f"[INFO] 총 {len(chunks)}개 청크 생성 완료")
    return chunks

def process_pdf_and_save_chunks() -> List[Dict[str, any]]:
    """PDF 다운로드 -> 텍스트 추출 -> 청킹 -> JSON 저장의 전체 과정을 실행합니다."""
    pdf_path = download_pdf()
    pages_data = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(pages_data)
    
    os.makedirs(os.path.dirname(CHUNKS_SAVE_PATH), exist_ok=True)
    with open(CHUNKS_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    print(f"[INFO] 청크 JSON 저장 완료: {CHUNKS_SAVE_PATH}")
    return chunks

if __name__ == "__main__":
    process_pdf_and_save_chunks()
