import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime
import io

# -------------------------------------------------------------------
# 1. 페이지 기본 설정 및 세션 상태(데이터 저장소) 초기화
# -------------------------------------------------------------------
st.set_page_config(page_title="형광 분석 및 완충효과 탐구 앱", layout="wide")

# 실험 데이터를 브라우저 세션에 저장 (새로고침 전까지 유지)
if "experiment_data" not in st.session_state:
    st.session_state.experiment_data = pd.DataFrame(
        columns=["측정 일시", "시료 종류", "pH", "평균 녹색 밝기", "최대 녹색 밝기"]
    )

# -------------------------------------------------------------------
# 2. UI 타이틀 및 탐구 소개
# -------------------------------------------------------------------
st.title("🧪 형광 특성 기반 pH 및 완충용액 분석 시스템")
st.markdown("""
이 앱은 **플루오레세인 나트륨**의 pH별 형광 사진을 분석하여, pH 변화에 따른 형광 세기를 정량적으로 측정하고 완충용액의 효과를 분석하는 고교 화학 탐구용 웹앱입니다.
- **AI 기능**: 컴퓨터 비전(Otsu 이진화) 알고리즘을 이용해 사진 속 **가장 밝은 형광 영역을 자동으로 인식**합니다.
""")
st.sidebar.header("📥 데이터 입력 및 사진 업로드")

# -------------------------------------------------------------------
# 3. 사이드바 - 실험 정보 입력 및 이미지 업로드
# -------------------------------------------------------------------
with st.sidebar:
    sample_type = st.selectbox(
        "1. 시료 종류 선택", 
        ["증류수 대조군", "아세트산 완충계", "인산 완충계", "기타 시료"]
    )
    
    # 완충용액 화학 탐구를 위해 pH는 소수점 입력 가능하도록 설정
    ph_value = st.number_input("2. 용액의 pH 입력", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
    
    # 이미지 파일 업로드 (여러 장 동시 업로드 지원)
    uploaded_files = st.file_uploader(
        "3. 형광 사진 업로드 (다중 선택 가능)", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

# -------------------------------------------------------------------
# 4. 메인 화면 - 이미지 프로세싱 및 데이터 추출
# -------------------------------------------------------------------
if uploaded_files:
    st.subheader("📸 업로드된 이미지 분석 및 AI ROI 자동 탐지")
    
    # 여러 이미지를 나란히 보여주기 위한 컬럼 생성
    cols = st.columns(len(uploaded_files))
    
    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx]:
            st.write(f"**파일명:** {uploaded_file.name}")
            
            # PIL 이미지로 변환 후 OpenCV 형식(numpy array)으로 변환
            image = Image.open(uploaded_file)
            img_array = np.array(image)
            
            # OpenCV는 BGR을 사용하므로 RGB 변환 처리 및 녹색 채널 분리
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            green_channel = img_bgr[:, :, 1]  # G 채널 추출
            
            # [AI/컴퓨터 비전 요소] Otsu 자동 이진화를 통해 형광이 발하는 밝은 영역만 마스킹
            # 주변 배경 노이즈를 제거하고 실제 형광 용액 부분만 정밀 추적함
            _, thresh = cv2.threshold(green_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 마스크된 영역(형광 영역) 내부의 픽셀 값만 추출
            fluorescent_pixels = green_channel[thresh == 255]
            
            if len(fluorescent_pixels) > 0:
                mean_green = np.mean(fluorescent_pixels)
                max_green = np.max(fluorescent_pixels)
            else:
                mean_green, max_green = 0, 0
            
            # 사용자에게 AI가 추출한 영역을 시각적으로 보여주기 위한 컨투어(테두리) 그리기
            img_contour = img_array.copy()
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img_contour, contours, -1, (255, 0, 0), 3) # 인식된 영역에 빨간 테두리 표시
            
            # 웹앱에 원본(테두리 표시) 및 AI 마스크 이미지 출력
            st.image(img_contour, caption="AI 형광 영역 인식 (빨간 테두리)", use_container_width=True)
            
            # 수치 결과 출력
            st.metric(label="평균 녹색 밝기 (0-255)", value=f"{mean_green:.2f}")
            st.metric(label="최대 녹색 밝기 (0-255)", value=f"{max_green}")
            
            # 데이터 추가 버튼
            if st.button(f"데이터 저장 ({uploaded_file.name[:10]}...)", key=f"btn_{idx}"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_data = pd.DataFrame([{
                    "측정 일시": now,
                    "시료 종류": sample_type,
                    "pH": ph_value,
                    "평균 녹색 밝기": round(mean_green, 2),
                    "최대 녹색 밝기": int(max_green)
                }])
                st.session_state.experiment_data = pd.concat([st.session_state.experiment_data, new_data], ignore_index=True)
                st.success(f"{uploaded_file.name} 데이터가 테이블에 추가되었습니다!")

st.sidebar.markdown("---")
if st.sidebar.button("데이터 초기화 🗑️"):
    st.session_state.experiment_data = pd.DataFrame(columns=["측정 일시", "시료 종류", "pH", "평균 녹색 밝기", "최대 녹색 밝기"])
    st.sidebar.warning("모든 데이터가 초기화되었습니다.")

# -------------------------------------------------------------------
# 5. 실험 데이터 테이블 및 그래프 시각화
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 실험 데이터 정리 및 그래프 분석")

df = st.session_state.experiment_data

if not df.empty:
    # 화면을 두 칸으로 분할 (왼쪽: 표, 오른쪽: 그래프)
    grid_left, grid_right = st.columns([1, 1])
    
    with grid_left:
        st.write("### 📝 실험 데이터 기록 표")
        st.dataframe(df, use_container_width=True)
        
        # CSV 다운로드 기능
        csv = df.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지 utf-8-sig
        st.download_button(
            label="📥 실험 데이터 CSV 다운로드",
            data=csv,
            file_name=f"형광분석_실험데이터_{datetime.now().strftime('%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    with grid_right:
        st.write("### 📈 pH - 형광 세기 시각화")
        
        # Matplotlib을 이용한 그래프 생성
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # 시료 종류별로 데이터를 나누어 그래프에 다른 색상/마커로 플로팅 (완충효과 비교 용이)
        types = df["시료 종류"].unique()
        for t in types:
            sub_df = df[df["시료 종류"] == t].sort_values(by="pH")
            ax.plot(sub_df["pH"], sub_df["평균 녹색 밝기"], marker='o', linestyle='-', label=t, markersize=8)
        
        ax.set_xlabel("pH")
        ax.set_ylabel("Fluorescence Intensity (Green Channel Mean)")
        ax.set_title("Fluorescence Intensity vs pH")
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 260)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        
        # 스트림릿에 그래프 출력
        st.pyplot(fig)
        
        # 그래프 이미지 다운로드 기능 추가
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)
        st.download_button(
            label="🖼️ 결과 그래프 이미지 저장",
            data=img_buf,
            file_name="형광_결과_그래프.png",
            mime="image/png"
        )
else:
    st.info("시이드바에서 조건을 입력하고 형광 사진을 업로드한 뒤 '데이터 저장' 버튼을 누르면 이 곳에 실시간 그래프와 데이터 표가 생성됩니다.")