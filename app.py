import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

st.set_page_config(
    page_title="플루오레세인 형광 분석",
    layout="wide"
)

st.title("🧪 플루오레세인 형광 분석")


# ==================================================
# 데이터 저장 공간
# ==================================================

columns = [
    "측정 일시",
    "시료 종류",
    "첨가 종류",
    "첨가 단계",
    "첨가량(mL)",
    "농도(%)",
    "pH",
    "평균 녹색 밝기",
    "최대 녹색 밝기",
    "포화 비율(%)"
]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=columns)


# ==================================================
# 실험 조건
# ==================================================

st.sidebar.header("실험 조건")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "농도 예비실험",
        "pH-형광 기준 시료",
        "pH 6 완충용액",
        "증류수 대조군",
        "기타 시료"
    ]
)


# --------------------------------------------------
# 농도 예비실험
# --------------------------------------------------

if sample_type == "농도 예비실험":

    concentration = st.sidebar.number_input(
        "플루오레세인 농도(%)",
        min_value=0.0000,
        value=0.0010,
        step=0.0010,
        format="%.4f"
    )

    ph = np.nan
    addition_type = "없음"
    addition_step = np.nan
    addition_volume = np.nan


# --------------------------------------------------
# 그 외 시료
# --------------------------------------------------

else:

    concentration = np.nan

    ph = st.sidebar.number_input(
        "실제 pH",
        min_value=0.0,
        max_value=14.0,
        value=6.0,
        step=0.1
    )

    # 완충용액과 증류수에서만 사용
    if sample_type in ["pH 6 완충용액", "증류수 대조군"]:

        addition_type = st.sidebar.selectbox(
            "첨가 종류",
            [
                "무첨가",
                "HCl",
                "NaOH"
            ]
        )

        if addition_type == "무첨가":

            addition_step = 0
            addition_volume = 0.0

        else:

            addition_step = st.sidebar.number_input(
                "첨가 단계",
                min_value=0,
                max_value=6,
                value=0,
                step=1
            )

            addition_volume = st.sidebar.number_input(
                "산·염기 첨가량(mL)",
                min_value=0.0,
                max_value=6.0,
                value=float(addition_step),
                step=1.0
            )

    else:

        addition_type = "없음"
        addition_step = np.nan
        addition_volume = np.nan


# ==================================================
# ROI 설정
# ==================================================

st.sidebar.header("ROI 설정")

st.sidebar.info(
    "현재는 증류수 대조군 실험 전의 임시 ROI입니다.\n\n"
    "최종 ROI는 전체 실험이 끝난 후 결정하세요."
)

x_start = st.sidebar.slider(
    "왼쪽 위치 (%)",
    0, 90, 20
)

x_end = st.sidebar.slider(
    "오른쪽 위치 (%)",
    10, 100, 80
)

y_start = st.sidebar.slider(
    "위쪽 위치 (%)",
    0, 90, 40
)

y_end = st.sidebar.slider(
    "아래쪽 위치 (%)",
    10, 100, 60
)


# ==================================================
# 사진 업로드
# ==================================================

uploaded_files = st.file_uploader(
    "형광 사진 업로드",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


# ==================================================
# 이미지 분석
# ==================================================

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


        # --------------------------------------------------
        # 녹색 채널
        # --------------------------------------------------

        green = roi[:, :, 1]


        # --------------------------------------------------
        # ROI 전체 평균
        # --------------------------------------------------

        roi_mean_green = float(np.mean(green))
        roi_max_green = int(np.max(green))

        roi_saturated = np.sum(green >= 250)

        roi_saturation_ratio = (
            roi_saturated / green.size
        ) * 100


        # --------------------------------------------------
        # Otsu 이진화
        # --------------------------------------------------

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
                caption="파란 사각형 = 현재 분석 ROI",
                use_container_width=True
            )


        with col2:

            st.metric(
                "ROI 전체 평균 녹색 밝기",
                f"{roi_mean_green:.2f}"
            )

            st.metric(
                "Otsu 평균 녹색 밝기",
                f"{mean_green:.2f}"
            )

            st.metric(
                "ROI 포화 픽셀 비율",
                f"{roi_saturation_ratio:.2f}%"
            )

            st.write(
                f"Otsu 임계값: {threshold:.1f}"
            )


        # --------------------------------------------------
        # 포화 경고
        # --------------------------------------------------

        if roi_saturation_ratio < 1:

            st.success(
                "ROI의 포화 픽셀이 거의 없습니다."
            )

        elif roi_saturation_ratio < 5:

            st.warning(
                "ROI에 일부 포화 픽셀이 있습니다."
            )

        else:

            st.error(
                "ROI에 포화 픽셀이 많습니다. "
                "형광 밝기 비교에 주의하세요."
            )


        # ==================================================
        # 데이터 저장
        # ==================================================

        if st.button(
            f"{file.name} 데이터 저장",
            key=f"save_{i}"
        ):

            new = pd.DataFrame([{

                "측정 일시":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "시료 종류":
                    sample_type,

                "첨가 종류":
                    addition_type,

                "첨가 단계":
                    addition_step,

                "첨가량(mL)":
                    addition_volume,

                "농도(%)":
                    concentration,

                "pH":
                    ph,

                # 현재는 ROI 전체 평균을 기본 데이터로 저장
                "평균 녹색 밝기":
                    round(roi_mean_green, 2),

                "최대 녹색 밝기":
                    roi_max_green,

                "포화 비율(%)":
                    round(
                        roi_saturation_ratio,
                        2
                    )
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


# ==================================================
# 저장 데이터
# ==================================================

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
        "CSV 다운로드",
        csv,
        "fluorescence_data.csv",
        "text/csv"
    )


    # ==================================================
    # 농도 - 형광 밝기
    # ==================================================

    conc_df = df[
        df["시료 종류"] == "농도 예비실험"
    ].dropna(
        subset=["농도(%)"]
    )


    if not conc_df.empty:

        st.subheader(
            "📈 플루오레세인 농도 - 형광 밝기"
        )

        graph_data = (
            conc_df
            .groupby("농도(%)")["평균 녹색 밝기"]
            .mean()
            .reset_index()
            .sort_values("농도(%)")
        )


        fig, ax = plt.subplots(
            figsize=(8, 5)
        )

        ax.plot(
            graph_data["농도(%)"],
            graph_data["평균 녹색 밝기"],
            marker="o"
        )

        ax.set_xlabel(
            "Fluorescein concentration (%)"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(
            0,
            255
        )

        ax.grid(
            alpha=0.3
        )

        st.pyplot(fig)


    # ==================================================
    # pH - 형광 밝기
    # ==================================================

    ph_df = df[
        df["시료 종류"] != "농도 예비실험"
    ].dropna(
        subset=["pH"]
    )


    if not ph_df.empty:

        st.subheader(
            "📈 pH - 형광 밝기"
        )


        # ----------------------------------------------
        # 시료 종류별 그래프
        # ----------------------------------------------

        fig, ax = plt.subplots(
            figsize=(9, 6)
        )


        for name in ph_df[
            "시료 종류"
        ].unique():

            sub = ph_df[
                ph_df["시료 종류"] == name
            ].sort_values("pH")


            ax.plot(
                sub["pH"],
                sub["평균 녹색 밝기"],
                marker="o",
                label=name
            )


        ax.set_xlabel(
            "pH"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(
            0,
            255
        )

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


    # ==================================================
    # pH 6 완충용액 - 첨가량 그래프
    # ==================================================

    buffer_df = df[
        df["시료 종류"] == "pH 6 완충용액"
    ].dropna(
        subset=["pH"]
    )


    if not buffer_df.empty:

        st.subheader(
            "🧪 pH 6 완충용액의 산·염기 첨가에 따른 변화"
        )


        # ----------------------------------------------
        # 산 첨가
        # ----------------------------------------------

        acid_df = buffer_df[
            buffer_df["첨가 종류"] == "HCl"
        ].sort_values(
            "첨가량(mL)"
        )


        if not acid_df.empty:

            st.write("### HCl 첨가")

            fig, ax = plt.subplots(
                figsize=(9, 5)
            )

            ax.plot(
                acid_df["첨가량(mL)"],
                acid_df["평균 녹색 밝기"],
                marker="o"
            )

            ax.set_xlabel(
                "HCl added (mL)"
            )

            ax.set_ylabel(
                "Mean green intensity"
            )

            ax.set_ylim(
                0,
                255
            )

            ax.grid(
                alpha=0.3
            )

            st.pyplot(fig)


        # ----------------------------------------------
        # NaOH 첨가
        # ----------------------------------------------

        base_df = buffer_df[
            buffer_df["첨가 종류"] == "NaOH"
        ].sort_values(
            "첨가량(mL)"
        )


        if not base_df.empty:

            st.write("### NaOH 첨가")

            fig, ax = plt.subplots(
                figsize=(9, 5)
            )

            ax.plot(
                base_df["첨가량(mL)"],
                base_df["평균 녹색 밝기"],
                marker="o"
            )

            ax.set_xlabel(
                "NaOH added (mL)"
            )

            ax.set_ylabel(
                "Mean green intensity"
            )

            ax.set_ylim(
                0,
                255
            )

            ax.grid(
                alpha=0.3
            )

            st.pyplot(fig)


        # ----------------------------------------------
        # pH 변화 그래프
        # ----------------------------------------------

        st.write(
            "### pH 변화에 따른 형광 밝기"
        )

        fig, ax = plt.subplots(
            figsize=(9, 5)
        )


        for name in buffer_df[
            "첨가 종류"
        ].unique():

            sub = buffer_df[
                buffer_df["첨가 종류"] == name
            ].sort_values(
                "pH"
            )


            ax.plot(
                sub["pH"],
                sub["평균 녹색 밝기"],
                marker="o",
                label=name
            )


        ax.set_xlabel(
            "Actual pH"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(
            0,
            255
        )

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


    # ==================================================
    # 증류수 대조군
    # ==================================================

    control_df = df[
        df["시료 종류"] == "증류수 대조군"
    ].dropna(
        subset=["pH"]
    )


    if not control_df.empty:

        st.subheader(
            "🔬 pH 6 완충용액 vs 증류수 대조군"
        )


        fig, ax = plt.subplots(
            figsize=(9, 6)
        )


        buffer_plot = buffer_df.sort_values(
            "pH"
        )

        control_plot = control_df.sort_values(
            "pH"
        )


        ax.plot(
            buffer_plot["pH"],
            buffer_plot["평균 녹색 밝기"],
            marker="o",
            label="pH 6 완충용액"
        )


        ax.plot(
            control_plot["pH"],
            control_plot["평균 녹색 밝기"],
            marker="o",
            label="증류수 대조군"
        )


        ax.set_xlabel(
            "Actual pH"
        )

        ax.set_ylabel(
            "Mean green intensity"
        )

        ax.set_ylim(
            0,
            255
        )

        ax.grid(
            alpha=0.3
        )

        ax.legend()

        st.pyplot(fig)


# ==================================================
# 데이터 초기화
# ==================================================

if st.sidebar.button(
    "데이터 초기화"
):

    st.session_state.data = pd.DataFrame(
        columns=columns
    )

    st.rerun()
