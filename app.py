import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="플루오레세인 형광 분석 앱",
    layout="wide"
)

st.title("🧪 플루오레세인 나트륨 형광 분석")
st.caption("pH 변화와 형광 밝기의 관계 및 완충용액의 완충 효과 분석")

# --------------------------------------------------
# 데이터 저장 공간
# --------------------------------------------------

columns = [
    "측정 일시",
    "시료 종류",
    "처리 종류",
    "산·염기 농도(M)",
    "첨가 단계",
    "첨가량(mL)",
    "플루오레세인 첨가 전 pH",
    "플루오레세인 첨가 후 최종 pH",
    "플루오레세인 나트륨 농도(%)",
    "평균 녹색 밝기",
    "최대 녹색 밝기",
    "포화 비율(%)",
    "파일명"
]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=columns)


# --------------------------------------------------
# 실험 조건 입력
# --------------------------------------------------

st.sidebar.header("🧪 실험 조건")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "pH-형광 기준 시료",
        "pH 6 완충용액",
        "증류수 대조군"
    ]
)

treatment = st.sidebar.selectbox(
    "처리 종류",
    [
        "무처리",
        "HCl",
        "NaOH"
    ]
)

# 산·염기 농도
if treatment == "무처리":
    reagent_concentration = 0.0
else:
    reagent_concentration = st.sidebar.number_input(
        f"{treatment} 농도 (M)",
        min_value=0.0001,
        max_value=1.0,
        value=0.01,
        step=0.01,
        format="%.4f"
    )

# 첨가 단계
step = st.sidebar.selectbox(
    "첨가 단계",
    [0, 1, 2, 3, 4, 5, 6]
)

# 첨가량
if treatment == "무처리":
    added_volume = 0.0
else:
    added_volume = st.sidebar.number_input(
        f"{treatment} 첨가량 (mL)",
        min_value=0.0,
        max_value=6.0,
        value=float(step),
        step=1.0,
        format="%.1f"
    )


# --------------------------------------------------
# pH 입력
# --------------------------------------------------

st.sidebar.header("📏 pH 측정값")

ph_before = st.sidebar.number_input(
    "플루오레세인 첨가 전 pH",
    min_value=0.0,
    max_value=14.0,
    value=6.0,
    step=0.1
)

ph_after = st.sidebar.number_input(
    "플루오레세인 첨가 후 최종 pH",
    min_value=0.0,
    max_value=14.0,
    value=6.0,
    step=0.1
)


# --------------------------------------------------
# 플루오레세인 조건
# --------------------------------------------------

st.sidebar.header("🟢 플루오레세인 나트륨")

st.sidebar.info(
    "0.01% 플루오레세인 나트륨 stock 1.0 mL\n\n"
    "시료 9.0 mL + stock 1.0 mL\n\n"
    "최종 부피 10.0 mL"
)

final_fluorescein_concentration = 0.001


# --------------------------------------------------
# ROI 설정
# --------------------------------------------------

st.sidebar.header("📐 ROI 설정")

st.sidebar.caption(
    "기존 실험에서 설정한 동일 ROI를 기본값으로 사용합니다."
)

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

    st.subheader("📷 형광 사진 분석")

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
                f"{file.name}: ROI 범위를 다시 설정하세요."
            )
            continue

        # --------------------------------------------------
        # 녹색 채널 분석
        # --------------------------------------------------

        green = roi[:, :, 1]

        threshold, mask = cv2.threshold(
            green,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        fluorescent = green[mask == 255]

        if len(fluorescent) > 0:

            mean_green = float(
                np.mean(fluorescent)
            )

            max_green = int(
                np.max(fluorescent)
            )

            saturated = np.sum(
                fluorescent >= 250
            )

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
                caption="파란 사각형 = 형광 분석 영역",
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

            if saturation_ratio < 1:

                st.success(
                    "포화가 거의 없습니다."
                )

            elif saturation_ratio < 5:

                st.warning(
                    "일부 픽셀이 포화되었습니다."
                )

            else:

                st.error(
                    "포화가 많습니다. "
                    "촬영 조건을 확인하세요."
                )


        # --------------------------------------------------
        # 데이터 저장
        # --------------------------------------------------

        if st.button(
            f"💾 {file.name} 데이터 저장",
            key=f"save_{i}"
        ):

            new = pd.DataFrame([{

                "측정 일시":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "시료 종류":
                    sample_type,

                "처리 종류":
                    treatment,

                "산·염기 농도(M)":
                    reagent_concentration,

                "첨가 단계":
                    step,

                "첨가량(mL)":
                    added_volume,

                "플루오레세인 첨가 전 pH":
                    ph_before,

                "플루오레세인 첨가 후 최종 pH":
                    ph_after,

                "플루오레세인 나트륨 농도(%)":
                    final_fluorescein_concentration,

                "평균 녹색 밝기":
                    round(mean_green, 2),

                "최대 녹색 밝기":
                    max_green,

                "포화 비율(%)":
                    round(saturation_ratio, 2),

                "파일명":
                    file.name
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

st.subheader("📊 실험 데이터")

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
        "📥 CSV 다운로드",
        csv,
        "fluorescence_experiment_data.csv",
        "text/csv"
    )


    # --------------------------------------------------
    # 그래프 1
    # 첨가량 - 실제 pH
    # --------------------------------------------------

    st.subheader("📈 첨가량에 따른 pH 변화")

    ph_plot_df = df[
        df["처리 종류"].isin(["HCl", "NaOH"])
    ].copy()

    if not ph_plot_df.empty:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        for name in ph_plot_df["시료 종류"].unique():

            for reagent in ph_plot_df[
                "처리 종류"
            ].unique():

                sub = ph_plot_df[
                    (ph_plot_df["시료 종류"] == name) &
                    (ph_plot_df["처리 종류"] == reagent)
                ].sort_values("첨가량(mL)")

                if not sub.empty:

                    ax.plot(
                        sub["첨가량(mL)"],
                        sub["플루오레세인 첨가 후 최종 pH"],
                        marker="o",
                        label=f"{name} - {reagent}"
                    )

        ax.set_xlabel(
            "Added volume (mL)"
        )

        ax.set_ylabel(
            "Final pH"
        )

        ax.set_ylim(0, 14)

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


    # --------------------------------------------------
    # 그래프 2
    # 첨가량 - 형광 밝기
    # --------------------------------------------------

    st.subheader(
        "📈 첨가량에 따른 형광 밝기 변화"
    )

    intensity_plot_df = df[
        df["처리 종류"].isin(["HCl", "NaOH"])
    ].copy()

    if not intensity_plot_df.empty:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        for name in intensity_plot_df[
            "시료 종류"
        ].unique():

            for reagent in intensity_plot_df[
                "처리 종류"
            ].unique():

                sub = intensity_plot_df[
                    (intensity_plot_df["시료 종류"] == name) &
                    (intensity_plot_df["처리 종류"] == reagent)
                ].sort_values("첨가량(mL)")

                if not sub.empty:

                    ax.plot(
                        sub["첨가량(mL)"],
                        sub["평균 녹색 밝기"],
                        marker="o",
                        label=f"{name} - {reagent}"
                    )

        ax.set_xlabel(
            "Added volume (mL)"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(0, 255)

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


    # --------------------------------------------------
    # 그래프 3
    # pH - 형광 밝기
    # --------------------------------------------------

    st.subheader(
        "📈 pH에 따른 형광 밝기 변화"
    )

    ph_intensity_df = df[
        df["플루오레세인 첨가 후 최종 pH"].notna()
    ].copy()

    if not ph_intensity_df.empty:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        for name in ph_intensity_df[
            "시료 종류"
        ].unique():

            sub = ph_intensity_df[
                ph_intensity_df["시료 종류"] == name
            ].sort_values(
                "플루오레세인 첨가 후 최종 pH"
            )

            ax.plot(
                sub[
                    "플루오레세인 첨가 후 최종 pH"
                ],
                sub["평균 녹색 밝기"],
                marker="o",
                label=name
            )

        ax.set_xlabel(
            "Final pH"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(0, 255)

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


    # --------------------------------------------------
    # 완충용액 vs 증류수 비교
    # --------------------------------------------------

    st.subheader(
        "🧪 완충용액과 증류수의 pH 변화 비교"
    )

    comparison_df = df[
        df["처리 종류"].isin(["HCl", "NaOH"])
    ].copy()

    if not comparison_df.empty:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        for name in comparison_df[
            "시료 종류"
        ].unique():

            sub = comparison_df[
                comparison_df["시료 종류"] == name
            ]

            if not sub.empty:

                grouped = (
                    sub.groupby(
                        "첨가량(mL)"
                    )[
                        "플루오레세인 첨가 후 최종 pH"
                    ]
                    .mean()
                    .reset_index()
                    .sort_values("첨가량(mL)")
                )

                ax.plot(
                    grouped["첨가량(mL)"],
                    grouped[
                        "플루오레세인 첨가 후 최종 pH"
                    ],
                    marker="o",
                    label=name
                )

        ax.set_xlabel(
            "Added volume (mL)"
        )

        ax.set_ylabel(
            "Final pH"
        )

        ax.set_ylim(0, 14)

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


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
