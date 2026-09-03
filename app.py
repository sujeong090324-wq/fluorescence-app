import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageOps
import plotly.express as px
import os

# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="플루오레세인 형광 분석",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 플루오레세인 나트륨 형광 분석")

st.caption(
    "ROI 내부의 평균 녹색 채널 밝기를 이용하여 "
    "pH 변화와 완충용액의 형광 변화를 분석합니다."
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
# 기존 데이터 불러오기
# =========================================================

if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)
else:
    df = pd.DataFrame(columns=COLUMNS)


# =========================================================
# 사이드바
# =========================================================

st.sidebar.header("실험 조건")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "농도 예비실험",
        "pH-형광 기준 시료",
        "pH 6 완충용액"
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
# 이미지 업로드
# =========================================================

uploaded_files = st.file_uploader(
    "실험 사진을 업로드하세요.",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


# =========================================================
# 이미지 분석
# =========================================================

if uploaded_files:

    st.subheader("사진 분석")

    for file in uploaded_files:

        # EXIF 방향 보정
        image = Image.open(file)
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")

        img_array = np.array(image)

        height, width = img_array.shape[:2]

        # ROI 좌표
        x1 = int(width * roi_left / 100)
        x2 = int(width * roi_right / 100)
        y1 = int(height * roi_top / 100)
        y2 = int(height * roi_bottom / 100)

        # 잘못된 ROI 방지
        if x2 <= x1 or y2 <= y1:
            st.error("ROI 범위가 잘못되었습니다.")
            continue

        roi = img_array[y1:y2, x1:x2]

        # 녹색 채널
        green = roi[:, :, 1]

        mean_green = float(np.mean(green))

        # -------------------------------------------------
        # 화면 표시
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                image,
                caption=file.name,
                use_container_width=True
            )

        with col2:

            st.write("### 분석 결과")

            st.metric(
                "평균 녹색 밝기",
                f"{mean_green:.2f}"
            )

            st.write(
                f"ROI: {roi_left}% ~ {roi_right}% × "
                f"{roi_top}% ~ {roi_bottom}%"
            )

            save_button = st.button(
                f"이 결과 저장하기",
                key=f"save_{file.name}"
            )

            if save_button:

                # 다음 첨가 단계 계산
                if addition_type == "없음":
                    step = 0
                else:
                    step = int(addition_volume)

                new_row = pd.DataFrame([{
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
                }])

                df = pd.concat(
                    [df, new_row],
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

    # 숫자형 변환
    df["pH"] = pd.to_numeric(
        df["pH"],
        errors="coerce"
    )

    df["첨가량(mL)"] = pd.to_numeric(
        df["첨가량(mL)"],
        errors="coerce"
    )

    df["평균 녹색 밝기"] = pd.to_numeric(
        df["평균 녹색 밝기"],
        errors="coerce"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        "⬇️ CSV 다운로드",
        data=csv_data,
        file_name="fluorescence_data.csv",
        mime="text/csv"
    )


# =========================================================
# 그래프
# =========================================================

st.divider()

st.header("📈 실험 결과 그래프")


# ---------------------------------------------------------
# ① HCl 첨가량에 따른 pH 변화
# ---------------------------------------------------------

hcl = df[
    (df["시료 종류"] == "pH 6 완충용액") &
    (df["첨가 종류"] == "HCl")
].copy()

if len(hcl) > 0:

    hcl = (
        hcl
        .dropna(subset=["첨가량(mL)", "pH"])
        .groupby("첨가량(mL)", as_index=False)["pH"]
        .mean()
        .sort_values("첨가량(mL)")
    )

    st.subheader("① HCl 첨가량에 따른 pH 변화")

    fig1 = px.line(
        hcl,
        x="첨가량(mL)",
        y="pH",
        markers=True,
        labels={
            "첨가량(mL)": "HCl 첨가량 (mL)",
            "pH": "pH"
        }
    )

    fig1.update_layout(
        height=450,
        xaxis=dict(dtick=1),
        yaxis=dict(range=[5.5, 6.2])
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )


# ---------------------------------------------------------
# ② HCl 첨가량에 따른 형광 밝기 변화
# ---------------------------------------------------------

if len(hcl) > 0:

    hcl_brightness = (
        df[
            (df["시료 종류"] == "pH 6 완충용액") &
            (df["첨가 종류"] == "HCl")
        ]
        .dropna(subset=["첨가량(mL)", "평균 녹색 밝기"])
        .groupby("첨가량(mL)", as_index=False)["평균 녹색 밝기"]
        .mean()
        .sort_values("첨가량(mL)")
    )

    st.subheader("② HCl 첨가량에 따른 형광 밝기 변화")

    fig2 = px.line(
        hcl_brightness,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "HCl 첨가량 (mL)",
            "평균 녹색 밝기": "Mean green intensity"
        }
    )

    fig2.update_layout(
        height=450,
        xaxis=dict(dtick=1)
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# ---------------------------------------------------------
# ③ NaOH 첨가량에 따른 pH 변화
# ---------------------------------------------------------

naoh = df[
    (df["시료 종류"] == "pH 6 완충용액") &
    (df["첨가 종류"] == "NaOH")
].copy()

if len(naoh) > 0:

    naoh = (
        naoh
        .dropna(subset=["첨가량(mL)", "pH"])
        .groupby("첨가량(mL)", as_index=False)["pH"]
        .mean()
        .sort_values("첨가량(mL)")
    )

    st.subheader("③ NaOH 첨가량에 따른 pH 변화")

    fig3 = px.line(
        naoh,
        x="첨가량(mL)",
        y="pH",
        markers=True,
        labels={
            "첨가량(mL)": "NaOH 첨가량 (mL)",
            "pH": "pH"
        }
    )

    fig3.update_layout(
        height=450,
        xaxis=dict(dtick=1)
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


# ---------------------------------------------------------
# ④ NaOH 첨가량에 따른 형광 밝기 변화
# ---------------------------------------------------------

if len(naoh) > 0:

    naoh_brightness = (
        df[
            (df["시료 종류"] == "pH 6 완충용액") &
            (df["첨가 종류"] == "NaOH")
        ]
        .dropna(subset=["첨가량(mL)", "평균 녹색 밝기"])
        .groupby("첨가량(mL)", as_index=False)["평균 녹색 밝기"]
        .mean()
        .sort_values("첨가량(mL)")
    )

    st.subheader("④ NaOH 첨가량에 따른 형광 밝기 변화")

    fig4 = px.line(
        naoh_brightness,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "NaOH 첨가량 (mL)",
            "평균 녹색 밝기": "Mean green intensity"
        }
    )

    fig4.update_layout(
        height=450,
        xaxis=dict(dtick=1)
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )


# ---------------------------------------------------------
# ⑤ pH 변화에 따른 완충용액 형광 밝기
# ---------------------------------------------------------

buffer = df[
    df["시료 종류"] == "pH 6 완충용액"
].copy()

if len(buffer) > 0:

    buffer = buffer.dropna(
        subset=["pH", "평균 녹색 밝기"]
    )

    st.subheader("⑤ pH 변화에 따른 완충용액의 형광 밝기")

    fig5 = px.scatter(
        buffer,
        x="pH",
        y="평균 녹색 밝기",
        color="첨가 종류",
        hover_data=[
            "첨가량(mL)"
        ],
        labels={
            "pH": "Actual pH",
            "평균 녹색 밝기": "Mean green intensity",
            "첨가 종류": "첨가"
        }
    )

    fig5.update_layout(
        height=500
    )

    st.plotly_chart(
        fig5,
        use_container_width=True
    )
