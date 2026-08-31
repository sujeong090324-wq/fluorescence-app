import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="플루오레세인 형광 분석",
    layout="wide"
)

st.title("🧪 플루오레세인 형광 분석")
st.caption("완충용액의 pH 변화에 따른 형광 밝기 분석용 임시 버전")


# --------------------------------------------------
# 데이터 저장 공간
# --------------------------------------------------

columns = [
    "측정 일시",
    "완충계",
    "처리 종류",
    "단계",
    "pH",
    "평균 녹색 밝기",
    "Otsu 평균 밝기",
    "최대 녹색 밝기",
    "포화 비율(%)"
]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=columns)


# --------------------------------------------------
# 실험 조건
# --------------------------------------------------

st.sidebar.header("🧪 실험 조건")

buffer_type = st.sidebar.selectbox(
    "완충계",
    [
        "아세트산 완충용액",
        "인산 완충용액",
        "증류수 대조군",
        "기타"
    ]
)

treatment = st.sidebar.selectbox(
    "처리 종류",
    [
        "무처리(0단계)",
        "HCl 첨가",
        "NaOH 첨가"
    ]
)

step = st.sidebar.number_input(
    "첨가 단계",
    min_value=0,
    max_value=6,
    value=0,
    step=1
)

ph = st.sidebar.number_input(
    "실제 pH",
    min_value=0.0,
    max_value=14.0,
    value=6.0,
    step=0.1,
    format="%.2f"
)


# --------------------------------------------------
# ROI 설정
# ※ 현재는 임시 설정
# ※ 증류수 대조군까지 끝난 뒤 최종 확정
# --------------------------------------------------

st.sidebar.header("🔍 ROI 설정")
st.sidebar.caption("현재는 임시 분석용입니다.")

x_start = st.sidebar.slider(
    "왼쪽 위치 (%)",
    0, 90, 27
)

x_end = st.sidebar.slider(
    "오른쪽 위치 (%)",
    10, 100, 47
)

y_start = st.sidebar.slider(
    "위쪽 위치 (%)",
    0, 90, 57
)

y_end = st.sidebar.slider(
    "아래쪽 위치 (%)",
    10, 100, 62
)


# --------------------------------------------------
# 사진 업로드
# --------------------------------------------------

uploaded_files = st.file_uploader(
    "형광 사진 업로드",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


# --------------------------------------------------
# 이미지 분석
# --------------------------------------------------

if uploaded_files:

    st.subheader("📷 사진 분석")

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
            st.error(
                f"{file.name}: ROI 범위가 올바르지 않습니다."
            )
            continue

        # --------------------------------------------------
        # 녹색 채널
        # --------------------------------------------------

        green = roi[:, :, 1]

        # ROI 전체 평균
        mean_green = float(np.mean(green))

        # 최대값
        max_green = int(np.max(green))

        # --------------------------------------------------
        # Otsu 분석
        # --------------------------------------------------

        threshold, mask = cv2.threshold(
            green,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        fluorescent = green[mask == 255]

        if len(fluorescent) > 0:
            otsu_mean = float(np.mean(fluorescent))

            saturated = np.sum(fluorescent >= 250)

            saturation_ratio = (
                saturated / len(fluorescent)
            ) * 100

        else:
            otsu_mean = 0
            saturation_ratio = 0


        # --------------------------------------------------
        # ROI 표시
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
                caption=f"{file.name} - 파란색 사각형 = 현재 ROI",
                use_container_width=True
            )

        with col2:

            st.metric(
                "ROI 전체 평균 녹색 밝기",
                f"{mean_green:.2f}"
            )

            st.metric(
                "Otsu 평균 밝기",
                f"{otsu_mean:.2f}"
            )

            st.metric(
                "최대 녹색 밝기",
                max_green
            )

            st.metric(
                "포화 비율",
                f"{saturation_ratio:.2f}%"
            )

            st.write(
                f"Otsu 임계값: {threshold:.1f}"
            )


        # --------------------------------------------------
        # 데이터 저장
        # --------------------------------------------------

        if st.button(
            f"💾 {file.name} 저장",
            key=f"save_{i}"
        ):

            new = pd.DataFrame([{

                "측정 일시":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "완충계":
                    buffer_type,

                "처리 종류":
                    treatment,

                "단계":
                    step,

                "pH":
                    ph,

                "평균 녹색 밝기":
                    round(mean_green, 2),

                "Otsu 평균 밝기":
                    round(otsu_mean, 2),

                "최대 녹색 밝기":
                    max_green,

                "포화 비율(%)":
                    round(saturation_ratio, 2)
            }])

            st.session_state.data = pd.concat(
                [
                    st.session_state.data,
                    new
                ],
                ignore_index=True
            )

            st.success(
                f"{file.name} 데이터가 저장되었습니다."
            )


# --------------------------------------------------
# 저장 데이터
# --------------------------------------------------

st.divider()

st.subheader("📊 저장된 실험 데이터")

df = st.session_state.data


if not df.empty:

    st.dataframe(
        df,
        use_container_width=True
    )


    # --------------------------------------------------
    # CSV 다운로드
    # --------------------------------------------------

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ CSV 다운로드",
        csv,
        "fluorescence_data.csv",
        "text/csv"
    )


    # ==================================================
    # pH - 형광 밝기 그래프
    # ==================================================

    st.divider()

    st.subheader(
        "📈 pH에 따른 형광 밝기 변화"
    )

    st.caption(
        "같은 완충계·처리 종류·단계의 반복 측정값은 평균하여 표시합니다."
    )


    # --------------------------------------------------
    # 평균 데이터 계산
    # --------------------------------------------------

    graph_data = (
        df
        .groupby(
            [
                "완충계",
                "처리 종류",
                "단계",
                "pH"
            ],
            as_index=False
        )
        .agg(
            {
                "평균 녹색 밝기": "mean",
                "Otsu 평균 밝기": "mean"
            }
        )
        .sort_values(
            [
                "완충계",
                "처리 종류",
                "pH"
            ]
        )
    )


    # --------------------------------------------------
    # ROI 전체 평균 그래프
    # --------------------------------------------------

    st.markdown(
        "### ① ROI 전체 평균 녹색 밝기"
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    for name, sub in graph_data.groupby(
        ["완충계", "처리 종류"]
    ):

        label = f"{name[0]} - {name[1]}"

        sub = sub.sort_values("pH")

        ax.plot(
            sub["pH"],
            sub["평균 녹색 밝기"],
            marker="o",
            linewidth=2,
            label=label
        )

    ax.set_xlabel(
        "pH",
        fontsize=12
    )

    ax.set_ylabel(
        "Mean green intensity",
        fontsize=12
    )

    ax.set_title(
        "pH - Fluorescence intensity"
    )

    ax.set_ylim(
        0,
        255
    )

    ax.grid(
        alpha=0.25
    )

    ax.legend()

    st.pyplot(fig)


    # --------------------------------------------------
    # Otsu 그래프
    # --------------------------------------------------

    st.markdown(
        "### ② Otsu 분석값 비교"
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    for name, sub in graph_data.groupby(
        ["완충계", "처리 종류"]
    ):

        label = f"{name[0]} - {name[1]}"

        sub = sub.sort_values("pH")

        ax.plot(
            sub["pH"],
            sub["Otsu 평균 밝기"],
            marker="o",
            linewidth=2,
            label=label
        )

    ax.set_xlabel(
        "pH",
        fontsize=12
    )

    ax.set_ylabel(
        "Otsu mean green intensity",
        fontsize=12
    )

    ax.set_title(
        "pH - Otsu fluorescence intensity"
    )

    ax.set_ylim(
        0,
        255
    )

    ax.grid(
        alpha=0.25
    )

    ax.legend()

    st.pyplot(fig)


    # --------------------------------------------------
    # 그래프용 평균 데이터 표
    # --------------------------------------------------

    st.subheader(
        "📋 그래프에 사용된 평균값"
    )

    st.dataframe(
        graph_data,
        use_container_width=True
    )


# --------------------------------------------------
# 데이터 초기화
# --------------------------------------------------

st.sidebar.divider()

if st.sidebar.button(
    "🗑️ 데이터 초기화"
):

    st.session_state.data = pd.DataFrame(
        columns=columns
    )

    st.rerun()
