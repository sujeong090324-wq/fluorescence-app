import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime
import io


# ============================================================
# 1. 페이지 기본 설정
# ============================================================

st.set_page_config(
    page_title="형광 분석 및 완충효과 탐구 앱",
    layout="wide"
)


# ============================================================
# 2. 세션 상태 초기화
# ============================================================

DATA_COLUMNS = [
    "측정 일시",
    "시료 종류",
    "플루오레세인 농도(%)",
    "pH",
    "평균 녹색 밝기",
    "최대 녹색 밝기"
]

if "experiment_data" not in st.session_state:
    st.session_state.experiment_data = pd.DataFrame(
        columns=DATA_COLUMNS
    )


# ============================================================
# 3. 메인 타이틀 및 설명
# ============================================================

st.title("🧪 형광 특성 기반 pH 및 완충용액 분석 시스템")

st.markdown(
    """
이 앱은 **플루오레세인 나트륨**의 형광 사진을 분석하여
플루오레세인 농도 및 pH 변화에 따른 형광 세기를 정량적으로 측정하고,
완충용액의 효과를 비교·분석하기 위한 고교 화학 탐구용 웹앱입니다.

- **농도 예비실험**: 플루오레세인의 적절한 실험 농도 선정
- **pH-형광 기준 시료**: pH와 형광 세기의 관계 측정
- **증류수 대조군**: 완충용액과 비교하기 위한 대조군
- **아세트산 완충계**: 아세트산-아세트산나트륨 완충용액
- **인산 완충계**: 인산염 완충용액
- **AI/컴퓨터 비전 기능**:
  Otsu 이진화를 이용하여 사진 속 밝은 형광 영역을 자동으로 탐지합니다.

형광 세기는 사진의 **녹색 채널(G channel)**을 기준으로 분석하며,
측정값은 **0~255 범위의 평균 녹색 밝기**로 나타냅니다.
"""
)


# ============================================================
# 4. 사이드바 입력
# ============================================================

st.sidebar.header("📥 데이터 입력 및 사진 업로드")

with st.sidebar:

    sample_type = st.selectbox(
        "1. 시료 종류 선택",
        [
            "농도 예비실험",
            "pH-형광 기준 시료",
            "증류수 대조군",
            "아세트산 완충계",
            "인산 완충계",
            "기타 시료"
        ]
    )

    # --------------------------------------------------------
    # 농도 예비실험은 농도를 입력
    # 나머지는 pH를 입력
    # --------------------------------------------------------

    if sample_type == "농도 예비실험":

        concentration = st.number_input(
            "2. 플루오레세인 농도(%)",
            min_value=0.000,
            max_value=1.000,
            value=0.010,
            step=0.001,
            format="%.3f"
        )

        ph_value = np.nan

        st.caption(
            "예: 0.1%, 0.05%, 0.02%, 0.01%를 비교할 때 "
            "각 시료의 실제 농도를 입력하세요."
        )

    else:

        ph_value = st.number_input(
            "2. 용액의 실제 pH 입력",
            min_value=0.0,
            max_value=14.0,
            value=7.0,
            step=0.1,
            format="%.2f"
        )

        concentration = np.nan

        st.caption(
            "목표 pH가 아니라 pH 미터로 측정한 "
            "실제 pH를 입력하는 것을 권장합니다."
        )


    # --------------------------------------------------------
    # 이미지 업로드
    # --------------------------------------------------------

    uploaded_files = st.file_uploader(
        "3. 형광 사진 업로드 (다중 선택 가능)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.markdown("---")

    # --------------------------------------------------------
    # 데이터 초기화
    # --------------------------------------------------------

    if st.button("데이터 초기화 🗑️"):

        st.session_state.experiment_data = pd.DataFrame(
            columns=DATA_COLUMNS
        )

        st.warning("모든 실험 데이터가 초기화되었습니다.")


# ============================================================
# 5. 이미지 분석
# ============================================================

if uploaded_files:

    st.subheader("📸 업로드된 이미지 분석 및 형광 영역 자동 탐지")

    # 사진 수가 너무 많으면 한 줄에 최대 3개
    num_cols = min(len(uploaded_files), 3)

    for start_idx in range(0, len(uploaded_files), num_cols):

        current_files = uploaded_files[
            start_idx:start_idx + num_cols
        ]

        cols = st.columns(len(current_files))

        for local_idx, uploaded_file in enumerate(current_files):

            idx = start_idx + local_idx

            with cols[local_idx]:

                st.write(f"**파일명:** {uploaded_file.name}")

                # ------------------------------------------------
                # 이미지 읽기
                # ------------------------------------------------

                image = Image.open(uploaded_file).convert("RGB")

                img_array = np.array(image)

                # RGB → BGR
                img_bgr = cv2.cvtColor(
                    img_array,
                    cv2.COLOR_RGB2BGR
                )

                # 녹색 채널 추출
                green_channel = img_bgr[:, :, 1]


                # ------------------------------------------------
                # Otsu 자동 이진화
                # ------------------------------------------------

                otsu_value, thresh = cv2.threshold(
                    green_channel,
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )


                # ------------------------------------------------
                # 형광 영역 픽셀 추출
                # ------------------------------------------------

                fluorescent_pixels = green_channel[
                    thresh == 255
                ]


                # ------------------------------------------------
                # 형광 밝기 계산
                # ------------------------------------------------

                if len(fluorescent_pixels) > 0:

                    mean_green = float(
                        np.mean(fluorescent_pixels)
                    )

                    max_green = int(
                        np.max(fluorescent_pixels)
                    )

                    pixel_count = int(
                        len(fluorescent_pixels)
                    )

                else:

                    mean_green = 0.0
                    max_green = 0
                    pixel_count = 0


                # ------------------------------------------------
                # 형광 영역 테두리 표시
                # ------------------------------------------------

                img_contour = img_array.copy()

                contours, _ = cv2.findContours(
                    thresh,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )

                cv2.drawContours(
                    img_contour,
                    contours,
                    -1,
                    (255, 0, 0),
                    3
                )


                # ------------------------------------------------
                # 이미지 표시
                # ------------------------------------------------

                st.image(
                    img_contour,
                    caption="자동 탐지된 형광 영역 (빨간 테두리)",
                    use_container_width=True
                )


                # ------------------------------------------------
                # 분석 결과 출력
                # ------------------------------------------------

                st.metric(
                    "평균 녹색 밝기 (0-255)",
                    f"{mean_green:.2f}"
                )

                st.metric(
                    "최대 녹색 밝기 (0-255)",
                    f"{max_green}"
                )

                st.caption(
                    f"Otsu 임계값: {otsu_value:.1f}"
                )

                st.caption(
                    f"분석된 형광 픽셀 수: {pixel_count:,}"
                )


                # ------------------------------------------------
                # 밝기 포화 경고
                # ------------------------------------------------

                if mean_green >= 245:

                    st.error(
                        "⚠️ 평균 밝기가 매우 높습니다. "
                        "카메라 포화 가능성이 있으므로 "
                        "더 낮은 농도를 검토하세요."
                    )

                elif mean_green >= 220:

                    st.warning(
                        "⚠️ 형광이 상당히 밝습니다. "
                        "사진의 포화 여부를 확인하세요."
                    )

                elif mean_green <= 30:

                    st.warning(
                        "⚠️ 형광 신호가 매우 약할 수 있습니다. "
                        "배경과 충분히 구분되는지 확인하세요."
                    )

                else:

                    st.success(
                        "✅ 밝기 값이 측정 가능한 범위에 있습니다."
                    )


                # ------------------------------------------------
                # 데이터 저장
                # ------------------------------------------------

                button_key = (
                    f"save_{idx}_"
                    f"{uploaded_file.name}_"
                    f"{sample_type}"
                )

                if st.button(
                    f"💾 데이터 저장",
                    key=button_key
                ):

                    now = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    new_data = pd.DataFrame(
                        [{
                            "측정 일시": now,
                            "시료 종류": sample_type,
                            "플루오레세인 농도(%)":
                                concentration,
                            "pH":
                                ph_value,
                            "평균 녹색 밝기":
                                round(mean_green, 2),
                            "최대 녹색 밝기":
                                max_green
                        }]
                    )

                    st.session_state.experiment_data = (
                        pd.concat(
                            [
                                st.session_state.experiment_data,
                                new_data
                            ],
                            ignore_index=True
                        )
                    )

                    st.success(
                        f"{uploaded_file.name} 데이터가 저장되었습니다!"
                    )


# ============================================================
# 6. 실험 데이터 표
# ============================================================

st.markdown("---")
st.subheader("📊 실험 데이터 정리 및 그래프 분석")

df = st.session_state.experiment_data


if not df.empty:

    st.write("### 📝 실험 데이터 기록 표")

    st.dataframe(
        df,
        use_container_width=True
    )


    # ========================================================
    # CSV 다운로드
    # ========================================================

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 실험 데이터 CSV 다운로드",
        data=csv,
        file_name=(
            "형광분석_실험데이터_"
            f"{datetime.now().strftime('%m%d_%H%M')}.csv"
        ),
        mime="text/csv"
    )


    # ========================================================
    # 7. 농도 예비실험 그래프
    # ========================================================

    concentration_df = df[
        df["시료 종류"] == "농도 예비실험"
    ].copy()

    if not concentration_df.empty:

        st.markdown("---")
        st.write("### 🧪 플루오레세인 농도 예비실험")

        concentration_df[
            "플루오레세인 농도(%)"
        ] = pd.to_numeric(
            concentration_df[
                "플루오레세인 농도(%)"
            ],
            errors="coerce"
        )

        concentration_df = concentration_df.dropna(
            subset=["플루오레세인 농도(%)"]
        )

        # 농도별 평균값과 표준편차 계산
        concentration_summary = (
            concentration_df
            .groupby("플루오레세인 농도(%)")[
                "평균 녹색 밝기"
            ]
            .agg(
                평균="mean",
                표준편차="std",
                측정횟수="count"
            )
            .reset_index()
            .sort_values(
                by="플루오레세인 농도(%)"
            )
        )

        st.write("#### 농도별 평균 밝기")

        st.dataframe(
            concentration_summary,
            use_container_width=True
        )


        # ----------------------------------------------------
        # 농도-형광 그래프
        # ----------------------------------------------------

        fig1, ax1 = plt.subplots(
            figsize=(7, 4)
        )

        ax1.plot(
            concentration_summary[
                "플루오레세인 농도(%)"
            ],
            concentration_summary["평균"],
            marker="o",
            linestyle="-"
        )

        ax1.set_xlabel(
            "Fluorescein concentration (%)"
        )

        ax1.set_ylabel(
            "Mean Green Intensity (0-255)"
        )

        ax1.set_title(
            "Fluorescence Intensity vs Concentration"
        )

        ax1.set_ylim(0, 260)

        ax1.grid(
            True,
            linestyle="--",
            alpha=0.6
        )

        st.pyplot(fig1)


        # ----------------------------------------------------
        # 그래프 저장
        # ----------------------------------------------------

        buf1 = io.BytesIO()

        fig1.savefig(
            buf1,
            format="png",
            bbox_inches="tight"
        )

        buf1.seek(0)

        st.download_button(
            label="🖼️ 농도-형광 그래프 저장",
            data=buf1,
            file_name="농도_형광_그래프.png",
            mime="image/png"
        )


        # ----------------------------------------------------
        # 농도 선정 안내
        # ----------------------------------------------------

        st.info(
            """
**농도 선정 기준**

1. 평균 밝기가 255에 지나치게 가까우면 피합니다.
2. 배경보다 충분히 밝아야 합니다.
3. 같은 농도를 3회 측정했을 때 값이 크게 흔들리지 않아야 합니다.
4. Otsu가 실제 형광 용액 영역을 제대로 탐지해야 합니다.
5. 너무 밝지도, 너무 어둡지도 않은 농도를 우선 선택합니다.

0.1%, 0.05%, 0.02%, 0.01%가 모두 너무 밝다면  
0.01%, 0.005%, 0.002%, 0.001% 범위로 추가 희석하여 비교할 수 있습니다.
"""
        )


    # ========================================================
    # 8. pH-형광 및 완충용액 그래프
    # ========================================================

    ph_df = df[
        df["시료 종류"] != "농도 예비실험"
    ].copy()

    if not ph_df.empty:

        ph_df["pH"] = pd.to_numeric(
            ph_df["pH"],
            errors="coerce"
        )

        ph_df = ph_df.dropna(
            subset=["pH"]
        )

        if not ph_df.empty:

            st.markdown("---")
            st.write(
                "### 📈 pH - 형광 세기 그래프"
            )

            fig2, ax2 = plt.subplots(
                figsize=(8, 5)
            )

            types = ph_df[
                "시료 종류"
            ].unique()

            for sample in types:

                sub_df = ph_df[
                    ph_df["시료 종류"] == sample
                ].sort_values(
                    by="pH"
                )

                ax2.plot(
                    sub_df["pH"],
                    sub_df["평균 녹색 밝기"],
                    marker="o",
                    linestyle="-",
                    label=sample
                )

            ax2.set_xlabel("pH")

            ax2.set_ylabel(
                "Fluorescence Intensity "
                "(Mean Green Channel)"
            )

            ax2.set_title(
                "Fluorescence Intensity vs pH"
            )

            ax2.set_xlim(0, 14)

            ax2.set_ylim(0, 260)

            ax2.grid(
                True,
                linestyle="--",
                alpha=0.6
            )

            ax2.legend()

            st.pyplot(fig2)


            # ------------------------------------------------
            # 그래프 다운로드
            # ------------------------------------------------

            buf2 = io.BytesIO()

            fig2.savefig(
                buf2,
                format="png",
                bbox_inches="tight"
            )

            buf2.seek(0)

            st.download_button(
                label="🖼️ pH-형광 그래프 저장",
                data=buf2,
                file_name="pH_형광_그래프.png",
                mime="image/png"
            )


else:

    st.info(
        """
사이드바에서 조건을 입력하고 형광 사진을 업로드한 뒤  
**'데이터 저장'** 버튼을 누르면 이곳에 실시간 데이터 표와 그래프가 생성됩니다.
"""
    )
