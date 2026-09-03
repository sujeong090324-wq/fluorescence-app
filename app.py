import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageOps, ImageDraw
import plotly.express as px
import os

st.set_page_config(
    page_title="플루오레세인 형광 분석",
    page_icon="🧪",
    layout="wide"
)

CSV_FILE = "fluorescence_data.csv"

COLUMNS = [
    "측정 일시",
    "시료 종류",
    "첨가 종류",
    "첨가 단계",
    "첨가량(mL)",
    "농도(%)",
    "pH",
    "평균 녹색 밝기"
]

# =========================================================
# 데이터 불러오기
# =========================================================

if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)
else:
    df = pd.DataFrame(columns=COLUMNS)

# 필요한 열이 없으면 생성
for col in COLUMNS:
    if col not in df.columns:
        df[col] = np.nan

# 숫자형 변환
for col in ["pH", "첨가량(mL)", "농도(%)", "평균 녹색 밝기"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# =========================================================
# 제목
# =========================================================

st.title("🧪 플루오레세인 나트륨 형광 분석")

st.caption(
    "ROI 내부의 평균 녹색 채널 밝기를 이용하여 "
    "pH 변화와 완충용액의 형광 변화를 분석합니다."
)


# =========================================================
# 실험 조건
# =========================================================

st.sidebar.header("실험 조건")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "pH-형광 기준 시료",
        "pH 6 완충용액",
        "농도 예비실험"
    ]
)

pH_value = st.sidebar.number_input(
    "pH",
    min_value=0.0,
    max_value=14.0,
    value=6.0,
    step=0.1
)

addition_type = st.sidebar.selectbox(
    "첨가 물질",
    ["없음", "HCl", "NaOH"]
)

addition_volume = st.sidebar.number_input(
    "첨가량 (mL)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=1.0
)

concentration = st.sidebar.number_input(
    "플루오레세인 나트륨 농도 (%)",
    min_value=0.0,
    value=0.001,
    step=0.0001,
    format="%.4f"
)


# =========================================================
# ROI
# =========================================================

st.sidebar.divider()
st.sidebar.header("ROI 설정")

roi_left = st.sidebar.slider(
    "왼쪽 (%)",
    0,
    100,
    35
)

roi_right = st.sidebar.slider(
    "오른쪽 (%)",
    0,
    100,
    65
)

roi_top = st.sidebar.slider(
    "위쪽 (%)",
    0,
    100,
    45
)

roi_bottom = st.sidebar.slider(
    "아래쪽 (%)",
    0,
    100,
    60
)


# =========================================================
# 사진 업로드
# =========================================================

uploaded_files = st.file_uploader(
    "실험 사진을 업로드하세요.",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


# =========================================================
# 사진 분석
# =========================================================

if uploaded_files:

    st.subheader("사진 분석")

    for i, file in enumerate(uploaded_files):

        # 사진 방향 자동 보정
        image = Image.open(file)
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")

        image_array = np.array(image)

        height, width = image_array.shape[:2]

        # ROI 좌표
        x1 = int(width * roi_left / 100)
        x2 = int(width * roi_right / 100)
        y1 = int(height * roi_top / 100)
        y2 = int(height * roi_bottom / 100)

        # ROI
        roi = image_array[y1:y2, x1:x2]

        # 녹색 채널
        green = roi[:, :, 1]

        # 평균 녹색 밝기
        mean_green = float(np.mean(green))

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                image,
                caption=file.name,
                use_container_width=True
            )

        with col2:

            st.metric(
                "평균 녹색 밝기",
                f"{mean_green:.2f}"
            )

            st.write(
                f"ROI: {roi_left}% ~ {roi_right}% × "
                f"{roi_top}% ~ {roi_bottom}%"
            )

            if st.button(
                "결과 저장",
                key=f"save_{i}_{file.name}"
            ):

                if addition_type == "없음":
                    step = 0
                else:
                    step = addition_volume

                new_data = {
                    "측정 일시": pd.Timestamp.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "시료 종류": sample_type,
                    "첨가 종류": addition_type,
                    "첨가 단계": step,
                    "첨가량(mL)": addition_volume,
                    "농도(%)": concentration,
                    "pH": pH_value,
                    "평균 녹색 밝기": round(mean_green, 2)
                }

                df = pd.concat(
                    [df, pd.DataFrame([new_data])],
                    ignore_index=True
                )

                df.to_csv(
                    CSV_FILE,
                    index=False,
                    encoding="utf-8-sig"
                )

                st.success("저장되었습니다.")


# =========================================================
# 저장된 데이터
# =========================================================

st.divider()

st.header("📊 저장된 실험 데이터")

if len(df) == 0:

    st.info("아직 저장된 데이터가 없습니다.")

else:

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ CSV 다운로드",
        data=df.to_csv(
            index=False,
            encoding="utf-8-sig"
        ),
        file_name="fluorescence_data.csv",
        mime="text/csv"
    )


# =========================================================
# 그래프
# =========================================================

st.divider()

st.header("📈 실험 결과")


# =========================================================
# ① 일반 용액 pH - 형광 밝기
# =========================================================

general = df[
    df["시료 종류"] == "pH-형광 기준 시료"
].dropna(
    subset=["pH", "평균 녹색 밝기"]
).copy()

if len(general) > 0:

    general = (
        general
        .groupby("pH", as_index=False)["평균 녹색 밝기"]
        .mean()
        .sort_values("pH")
    )

    st.subheader(
        "① pH 변화에 따른 형광 밝기"
    )

    fig1 = px.line(
        general,
        x="pH",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "pH": "pH",
            "평균 녹색 밝기": "평균 녹색 밝기"
        }
    )

    fig1.update_layout(
        height=450
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )


# =========================================================
# 완충용액 데이터
# =========================================================

buffer = df[
    df["시료 종류"] == "pH 6 완충용액"
].copy()

buffer["pH"] = pd.to_numeric(
    buffer["pH"],
    errors="coerce"
)

buffer["첨가량(mL)"] = pd.to_numeric(
    buffer["첨가량(mL)"],
    errors="coerce"
)

buffer["평균 녹색 밝기"] = pd.to_numeric(
    buffer["평균 녹색 밝기"],
    errors="coerce"
)


# =========================================================
# HCl
# =========================================================

hcl = buffer[
    buffer["첨가 종류"] == "HCl"
].dropna(
    subset=[
        "첨가량(mL)",
        "pH",
        "평균 녹색 밝기"
    ]
).copy()

if len(hcl) > 0:

    hcl = (
        hcl
        .groupby("첨가량(mL)", as_index=False)
        .agg({
            "pH": "mean",
            "평균 녹색 밝기": "mean"
        })
        .sort_values("첨가량(mL)")
    )

    # -----------------------------------------------------
    # ② HCl 첨가량 - pH
    # -----------------------------------------------------

    st.subheader(
        "② HCl 첨가량에 따른 pH 변화"
    )

    fig2 = px.line(
        hcl,
        x="첨가량(mL)",
        y="pH",
        markers=True,
        labels={
            "첨가량(mL)": "HCl 첨가량 (mL)",
            "pH": "pH"
        }
    )

    fig2.update_layout(
        height=450
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ③ HCl 첨가량 - 형광
    # -----------------------------------------------------

    st.subheader(
        "③ HCl 첨가량에 따른 형광 밝기 변화"
    )

    fig3 = px.line(
        hcl,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "HCl 첨가량 (mL)",
            "평균 녹색 밝기": "평균 녹색 밝기"
        }
    )

    fig3.update_layout(
        height=450
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


# =========================================================
# NaOH
# =========================================================

naoh = buffer[
    buffer["첨가 종류"] == "NaOH"
].dropna(
    subset=[
        "첨가량(mL)",
        "pH",
        "평균 녹색 밝기"
    ]
).copy()

if len(naoh) > 0:

    naoh = (
        naoh
        .groupby("첨가량(mL)", as_index=False)
        .agg({
            "pH": "mean",
            "평균 녹색 밝기": "mean"
        })
        .sort_values("첨가량(mL)")
    )

    # -----------------------------------------------------
    # ④ NaOH 첨가량 - pH
    # -----------------------------------------------------

    st.subheader(
        "④ NaOH 첨가량에 따른 pH 변화"
    )

    fig4 = px.line(
        naoh,
        x="첨가량(mL)",
        y="pH",
        markers=True,
        labels={
            "첨가량(mL)": "NaOH 첨가량 (mL)",
            "pH": "pH"
        }
    )

    fig4.update_layout(
        height=450
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ⑤ NaOH 첨가량 - 형광
    # -----------------------------------------------------

    st.subheader(
        "⑤ NaOH 첨가량에 따른 형광 밝기 변화"
    )

    fig5 = px.line(
        naoh,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "NaOH 첨가량 (mL)",
            "평균 녹색 밝기": "평균 녹색 밝기"
        }
    )

    fig5.update_layout(
        height=450
    )

    st.plotly_chart(
        fig5,
        use_container_width=True
    )


# =========================================================
# ⑥ 완충용액 pH - 형광 밝기
# =========================================================

buffer_graph = buffer.dropna(
    subset=[
        "pH",
        "평균 녹색 밝기"
    ]
).copy()

if len(buffer_graph) > 0:

    st.subheader(
        "⑥ pH 변화에 따른 완충용액의 형광 밝기"
    )

    fig6 = px.scatter(
        buffer_graph,
        x="pH",
        y="평균 녹색 밝기",
        color="첨가 종류",
        hover_data=["첨가량(mL)"],
        labels={
            "pH": "pH",
            "평균 녹색 밝기": "평균 녹색 밝기",
            "첨가 종류": "첨가 물질"
        }
    )

    fig6.update_layout(
        height=500
    )

    st.plotly_chart(
        fig6,
        use_container_width=True
    )
