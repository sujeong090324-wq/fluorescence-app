import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="형광 분석 앱", layout="wide")
st.title("🧪 플루오레세인 형광 분석")

# --------------------------------------------------
# 데이터 저장 공간
# --------------------------------------------------

columns = [
    "측정 일시", "시료 종류", "농도(%)", "pH",
    "평균 녹색 밝기", "최대 녹색 밝기", "포화 비율(%)"
]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=columns)


# --------------------------------------------------
# 입력
# --------------------------------------------------

st.sidebar.header("실험 조건")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "농도 예비실험",
        "pH-형광 기준 시료",
        "증류수 대조군",
        "아세트산 완충계",
        "인산 완충계",
        "기타 시료"
    ]
)

if sample_type == "농도 예비실험":
    concentration = st.sidebar.number_input(
        "플루오레세인 농도(%)",
        min_value=0.0000,
        value=0.0010,
        step=0.0010,
        format="%.4f"
    )
    ph = np.nan
else:
    ph = st.sidebar.number_input(
        "실제 pH",
        min_value=0.0,
        max_value=14.0,
        value=7.0,
        step=0.1
    )
    concentration = np.nan


# --------------------------------------------------
# ROI 설정
# 사진에서 시험관 부분만 분석
# --------------------------------------------------

st.sidebar.header("ROI 설정")

x_start = st.sidebar.slider("왼쪽 위치 (%)", 0, 90, 10)
x_end = st.sidebar.slider("오른쪽 위치 (%)", 10, 100, 35)

y_start = st.sidebar.slider("위쪽 위치 (%)", 0, 90, 5)
y_end = st.sidebar.slider("아래쪽 위치 (%)", 10, 100, 95)


uploaded_files = st.file_uploader(
    "형광 사진 업로드",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


# --------------------------------------------------
# 이미지 분석
# --------------------------------------------------

if uploaded_files:

    for i, file in enumerate(uploaded_files):

        image = Image.open(file).convert("RGB")
        img = np.array(image)

        h, w = img.shape[:2]

        x1 = int(w * x_start / 100)
        x2 = int(w * x_end / 100)

        y1 = int(h * y_start / 100)
        y2 = int(h * y_end / 100)

        roi = img[y1:y2, x1:x2]

        if roi.size == 0:
            st.error("ROI 범위를 다시 설정하세요.")
            continue

        # 녹색 채널
        green = roi[:, :, 1]

        # Otsu 이진화
        threshold, mask = cv2.threshold(
            green,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        fluorescent = green[mask == 255]

        if len(fluorescent) > 0:

            mean_green = float(np.mean(fluorescent))
            max_green = int(np.max(fluorescent))

            saturated = np.sum(fluorescent >= 250)

            saturation_ratio = (
                saturated / len(fluorescent)
            ) * 100

        else:

            mean_green = 0
            max_green = 0
            saturation_ratio = 0


        # --------------------------------------------------
        # 분석 영역 표시
        # --------------------------------------------------

        display = img.copy()

        cv2.rectangle(
            display,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            5
        )

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                display,
                caption="빨간 사각형 = 분석 영역",
                use_container_width=True
            )

        with col2:

            st.metric(
                "평균 녹색 밝기",
                f"{mean_green:.2f}"
            )

            st.metric(
                "최대 녹색 밝기",
                max_green
            )

            st.metric(
                "포화 픽셀 비율",
                f"{saturation_ratio:.2f}%"
            )

            st.write(
                f"Otsu 임계값: {threshold:.1f}"
            )

            # 간단한 포화 판정
            if saturation_ratio < 1:
                st.success("포화가 거의 없습니다.")

            elif saturation_ratio < 5:
                st.warning("일부 픽셀이 포화되었습니다.")

            else:
                st.error("포화가 많습니다. 촬영 조건 또는 농도를 조정하세요.")


        # --------------------------------------------------
        # 데이터 저장
        # --------------------------------------------------

        if st.button(
            f"{file.name} 데이터 저장",
            key=f"save_{i}"
        ):

            new = pd.DataFrame([{
                "측정 일시":
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                "시료 종류":
                    sample_type,

                "농도(%)":
                    concentration,

                "pH":
                    ph,

                "평균 녹색 밝기":
                    round(mean_green, 2),

                "최대 녹색 밝기":
                    max_green,

                "포화 비율(%)":
                    round(saturation_ratio, 2)
            }])

            st.session_state.data = pd.concat(
                [st.session_state.data, new],
                ignore_index=True
            )

            st.success("저장되었습니다.")


# --------------------------------------------------
# 저장 데이터
# --------------------------------------------------

st.divider()
st.subheader("📊 실험 데이터")

df = st.session_state.data

if not df.empty:

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "fluorescence_data.csv",
        "text/csv"
    )


    # --------------------------------------------------
    # 농도 예비실험 그래프
    # --------------------------------------------------

    conc_df = df[
        df["시료 종류"] == "농도 예비실험"
    ].dropna(subset=["농도(%)"])

    if not conc_df.empty:

        st.subheader("농도 - 형광 밝기")

        graph_data = (
            conc_df
            .groupby("농도(%)")["평균 녹색 밝기"]
            .mean()
            .reset_index()
            .sort_values("농도(%)")
        )

        fig, ax = plt.subplots()

        ax.plot(
            graph_data["농도(%)"],
            graph_data["평균 녹색 밝기"],
            marker="o"
        )

        ax.set_xlabel("Fluorescein concentration (%)")
        ax.set_ylabel("Mean green intensity")
        ax.set_ylim(0, 255)

        st.pyplot(fig)


    # --------------------------------------------------
    # pH - 형광 그래프
    # --------------------------------------------------

    ph_df = df[
        df["시료 종류"] != "농도 예비실험"
    ].dropna(subset=["pH"])

    if not ph_df.empty:

        st.subheader("pH - 형광 밝기")

        fig, ax = plt.subplots()

        for name in ph_df["시료 종류"].unique():

            sub = ph_df[
                ph_df["시료 종류"] == name
            ].sort_values("pH")

            ax.plot(
                sub["pH"],
                sub["평균 녹색 밝기"],
                marker="o",
                label=name
            )

        ax.set_xlabel("pH")
        ax.set_ylabel("Mean green intensity")
        ax.set_ylim(0, 255)
        ax.legend()

        st.pyplot(fig)


# --------------------------------------------------
# 초기화
# --------------------------------------------------

if st.sidebar.button("데이터 초기화"):

    st.session_state.data = pd.DataFrame(
        columns=columns
    )

    st.rerun()
