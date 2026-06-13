import streamlit as st
import requests
import pandas as pd
import time

st.title("💊 NutriFit 2030 - 전체 데이터 자동 동기화")
st.write("식약처 API의 1,000건 제한을 자동으로 극복하고 전체 데이터를 수집합니다.")

# 유저가 제공한 실제 인증키와 서비스 ID 고정
API_KEY = "be08162c9d464d6998a5"
SERVICE_ID = "C003"

if st.button("🔄 식약처 전체 데이터 가져오기 (무제한 연동)"):
    # [Step 1] 전체 개수를 알아내기 위한 첫 번째 정찰 요청 (딱 1개만 요청해봅니다)
    recon_url = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE_ID}/json/1/1"
    
    with st.spinner("식약처 창고 확인 중..."):
        try:
            response = requests.get(recon_url)
            if response.status_code == 200:
                recon_data = response.json()
                
                if SERVICE_ID in recon_data:
                    # API가 영수증처럼 보내준 진짜 전체 데이터 개수(끝번호) 추출
                    total_count = int(recon_data[SERVICE_ID]['list_total_count'])
                    st.info(f"📊 현재 식약처 창고에 등록된 데이터는 총 {total_count:,}건입니다.")
                    
                    # [Step 2] 반복 수집을 위한 바구니 및 게이지 바 준비
                    all_rows = []
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    # 1부터 전체 개수까지 1,000 단위로 건너뛰며 반복문 실행
                    # 예: 1~1000, 1001~2000, 2001~3000 ...
                    for start_idx in range(1, total_count + 1, 1000):
                        # 끝 번호가 총 개수를 넘지 않도록 제한
                        end_idx = min(start_idx + 999, total_count)
                        
                        # 다이내믹 URL 자동 조립
                        target_url = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE_ID}/json/{start_idx}/{end_idx}"
                        
                        # 대시보드 화면에 현재 수집 현황 실시간 표시
                        progress_text.text(f"🚀 실시간 수집 중: {start_idx:,}번 ~ {end_idx:,}번 (전체 {total_count:,}건 중)")
                        
                        # 데이터 요청
                        loop_response = requests.get(target_url)
                        
                        if loop_response.status_code == 200:
                            loop_data = loop_response.json()
                            if SERVICE_ID in loop_data and 'row' in loop_data[SERVICE_ID]:
                                row_data = loop_data[SERVICE_ID]['row']
                                # 가져온 1,000개 조각을 큰 바구니에 차곡차곡 누적
                                all_rows.extend(row_data)
                            else:
                                st.warning(f"⚠️ {start_idx} ~ {end_idx} 구간에 데이터가 없습니다.")
                        else:
                            st.error(f"❌ 서버 연결 실패 (구간: {start_idx} ~ {end_idx})")
                            break
                        
                        # 진행 게이지 바 업데이트
                        progress_bar.progress(end_idx / total_count)
                        
                        # 공공기관 서버 과부하 방지 및 안정적인 수집을 위한 미세한 숨고르기 (0.2초)
                        time.sleep(0.2)
                    
                    # [Step 3] 수집된 모든 조각을 하나의 표로 병합 및 저장
                    if all_rows:
                        final_df = pd.DataFrame(all_rows)
                        progress_text.text("✨ 전체 데이터 수집 및 통합 완료!")
                        st.success(f"축하합니다! 총 {len(final_df):,}건의 모든 데이터를 결합했습니다.")
                        
                        # 대시보드 화면에 전체 표 출력
                        st.dataframe(final_df, use_container_width=True)
                        
                        # 안티그래비티 환경 내에 CSV 파일로 영구 저장 (★매우 중요★)
                        final_df.to_csv("nutrifit_total_data.csv", index=False, encoding="utf-8-sig")
                        st.info("💾 안티그래비티 워크스페이스에 'nutrifit_total_data.csv' 파일로 저장이 완료되었습니다. 이제 다음 분석부터는 매번 API를 수집하느라 기다릴 필요 없이 이 CSV 파일만 불러와서 쓰시면 됩니다!")
                    else:
                        st.error("수집된 데이터가 존재하지 않습니다.")
                else:
                    st.error("인증키가 올바르지 않거나 서비스 ID(C003)를 확인할 수 없습니다.")
            else:
                st.error(f"최초 서버 연결 실패 (에러 코드: {response.status_code})")
        except Exception as e:
            st.error(f"코드 실행 중 에러 발생: {e}")
