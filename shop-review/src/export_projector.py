import os
import re
import unicodedata
import pandas as pd
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# PyTorch 멀티스레딩 활성화로 저사양 CPU 인코딩 속도 최적화
torch.set_num_threads(os.cpu_count() or 4)

# 1. 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "shop-review.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "projector")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TENSORS_PATH = os.path.join(OUTPUT_DIR, "tensors.tsv")
METADATA_PATH = os.path.join(OUTPUT_DIR, "metadata.tsv")

print(f"1. 데이터 로드: {DATA_PATH}")
df = pd.read_csv(DATA_PATH, encoding='utf-8')

# 유니코드 NFC 정규화
def normalize_text(text):
    if pd.isna(text):
        return ""
    return unicodedata.normalize('NFC', str(text))

df['title_clean'] = df['title'].apply(normalize_text)
df['content_clean'] = df['content'].apply(normalize_text)
df['product_clean'] = df['product'].apply(normalize_text)
df['mallName_clean'] = df['mallName'].apply(normalize_text)

# HTML 태그 및 앰퍼샌드 엔티티 정제 함수 (형태소 분석기 미사용)
def clean_html(text):
    if not text:
        return ""
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', text)
    # HTML 엔티티 제거 (&nbsp;, &gt; 등)
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
    # 연속된 공백 하나로 정제
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['title_processed'] = df['title_clean'].apply(clean_html)
df['content_processed'] = df['content_clean'].apply(clean_html)
df['product_processed'] = df['product_clean'].apply(clean_html)
df['mallName_processed'] = df['mallName_clean'].apply(clean_html)

# 임베딩용 통합 텍스트 (제목 + 내용)
df['embedding_text'] = df['title_processed'] + " " + df['content_processed']
df['embedding_text'] = df['embedding_text'].str.strip()
df['embedding_text'] = df['embedding_text'].replace('', '제목 및 내용 없음')

print(f"총 {len(df):,}건의 리뷰 데이터 전처리 완료.")

# 2. 사전 학습된 초경량 한국어/다국어 문장 임베딩 모델 로드 (저사양 노트북 고속 연산)
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
print(f"2. 저사양 고속 사전 학습 임베딩 모델 로드 중: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

print("3. 리뷰 텍스트 문장 임베딩 벡터 고속 변환 시작...")
with torch.no_grad():
    embeddings = model.encode(
        df['embedding_text'].tolist(),
        batch_size=256,
        show_progress_bar=True,
        normalize_embeddings=True
    )

print(f"임베딩 완료: shape = {embeddings.shape}")

# 4. Projector용 TSV 파일 저장

# A. tensors.tsv (헤더, 인덱스 없음 / 탭 구분)
print(f"4-A. tensors.tsv 파일 저장 중: {TENSORS_PATH}")
np.savetxt(TENSORS_PATH, embeddings, delimiter='\t', fmt='%.6f')

# B. metadata.tsv (첫 줄 헤더 포함 / TSV 깨짐 방지를 위해 줄바꿈 및 탭 치환)
print(f"4-B. metadata.tsv 파일 저장 중: {METADATA_PATH}")

def sanitize_tsv_cell(text):
    if not text:
        return ""
    return str(text).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ').strip()

metadata_rows = []
for idx, row in df.iterrows():
    title_label = sanitize_tsv_cell(row['title_processed'])
    if not title_label:
        title_label = "(제목없음)"
        
    product_cat = sanitize_tsv_cell(row['product_processed'])
    if not product_cat:
        product_cat = "미지정"
        
    mall_cat = sanitize_tsv_cell(row['mallName_processed'])
    if not mall_cat:
        mall_cat = "미지정"
        
    full_text = sanitize_tsv_cell(f"[제목] {row['title_processed']} | [내용] {row['content_processed']}")
    
    metadata_rows.append({
        'Title': title_label,
        'Product': product_cat,
        'MallName': mall_cat,
        'Title_and_Content': full_text
    })

metadata_df = pd.DataFrame(metadata_rows)
metadata_df.to_csv(METADATA_PATH, sep='\t', index=False, encoding='utf-8-sig')

print("\n=== Tensor Board / TensorFlow Projector용 파일 생성 성공 완수 ===")
print(f"- Tensors File: {TENSORS_PATH} ({os.path.getsize(TENSORS_PATH)/1024/1024:.2f} MB)")
print(f"- Metadata File: {METADATA_PATH} ({os.path.getsize(METADATA_PATH)/1024/1024:.2f} MB)")
