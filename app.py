import streamlit as st
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
from io import BytesIO


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="플루오레세인 형광 분석",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 플루오레세인 형광 사진 분석")
st.caption("ROI 영역의 평균 녹색 밝기를 이용하여 플루오레세인의 형광 세기를 분석합니다.")


# =========================================================
# 세션 상태
# =========================================================

if "results" not in st.session_state:
    st.session_state.results = {}

if "roi_values" not in st.session_state:
    st.session_state.roi_values = {}


# =========================================================
# 함수
# =========================================================

def pil_to_cv2(pil_image):
    """
    PIL 이미지를 OpenCV RGB 배열로 변환
    EXIF 회전 정보를 반영하여 휴대폰 사진 방향 문제 방지
    """
    pil_image = ImageOps.exif_transpose(pil_image)
    pil_image = pil_image.convert("RGB")
    return np.array(pil_image)


def make_roi_image(image_rgb, left, right, top, bottom):
    """
    원본 사진 위에 ROI 박스를 표시
    """
    img = image_rgb.copy()

    h, w = img.shape[:2]

    x1 = int(w * left / 100)
    x2 = int(w * right / 100)
    y1 = int(h * top / 100)
    y2 = int(h * bottom / 100)

    # 좌표 안전 처리
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w - 1))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h - 1))

    # ROI 사각형
    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        (255, 0, 0),
        6
    )

    # ROI 내부에 표시
    cv2.putText(
        img,
        "ROI",
        (x1 + 10, y1 + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 0, 0),
        3,
        cv2.LINE_AA
    )

    return img, (x1, x2, y1, y2)


def analyze_roi(image_rgb, left, right, top, bottom):
    """
    ROI 영역의 평균 녹색 밝기 분석
    """
    h, w = image_rgb.shape[:2]

    x1 = int(w * left / 100)
    x2 = int(w * right / 100)
    y1 = int(h * top / 100)
    y2 = int(h * bottom / 100)

    # 안전 처리
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h))

    roi = image_rgb[y1:y2, x1:x2]

    if roi.size == 0:
        return None

    # RGB에서 G 채널
    green = roi[:, :, 1]

    mean_green = float(np.mean(green))
    max_green = int(np.max(green))

    # 포화 비율
    saturation_ratio = float(np.mean(green >= 255) * 100)

    return {
        "평균 녹색 밝기": round(mean_green, 2),
        "최대 녹색 밝기": max_green,
        "포화 비율(%)": round(saturation_ratio, 2)
    }


def get_numeric_pH(df):
    """
    pH를 숫자로 변환
    """
    if "pH" in df.columns:
        df["pH"] = pd.to_numeric(df["pH"], errors="coerce")

    return df


# =========================================================
# 사이드바
# =========================================================

st.sidebar.header("⚙️ 기본 설정")

sample_type = st.sidebar.selectbox(
    "시료 종류",
    [
        "농도 예비실험",
        "pH-형광 기준 시료",
        "pH 6 완충용액",
        "기타 시료"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "💡 완충용액 사진은 사진마다 위치가 조금씩 다르므로 "
    "사진을 하나씩 선택하여 ROI를 조절하고 저장하세요."
)


# =========================================================
# 사진 업로드
# =========================================================

uploaded_files = st.file_uploader(
    "📷 분석할 사진을 업로드하세요.",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


if uploaded_files:

    # -----------------------------------------------------
    # 사진 목록
    # -----------------------------------------------------

    file_names = [
        f"{i + 1}. {file.name}"
        for i, file in enumerate(uploaded_files)
    ]

    selected_index = st.selectbox(
        "🔎 분석할 사진 선택",
        range(len(uploaded_files)),
        format_func=lambda x: file_names[x]
    )

    selected_file = uploaded_files[selected_index]

    # 사진별 고유 키
    image_key = f"{selected_index}_{selected_file.name}"

    # -----------------------------------------------------
    # 이미지 읽기
    # -----------------------------------------------------

    selected_file.seek(0)
    pil_image = Image.open(selected_file)

    image_rgb = pil_to_cv2(pil_image)

    # -----------------------------------------------------
    # 사진별 기본 ROI
    # -----------------------------------------------------

    if image_key not in st.session_state.roi_values:

        # 완충용액 사진 기본값
        st.session_state.roi_values[image_key] = {
            "left": 35,
            "right": 65,
            "top": 45,
            "bottom": 60
        }

    current_roi = st.session_state.roi_values[image_key]

    # -----------------------------------------------------
    # 사진 정보
    # -----------------------------------------------------

    st.subheader("📸 현재 사진")

    st.write(f"**파일:** `{selected_file.name}`")

    h, w = image_rgb.shape[:2]

    st.caption(f"사진 크기: {w} × {h} px")

    # -----------------------------------------------------
    # ROI 설정
    # -----------------------------------------------------

    st.subheader("🎯 ROI 설정")

    col1, col2 = st.columns(2)

    with col1:

        left = st.slider(
            "왼쪽 (%)",
            0,
            90,
            current_roi["left"],
            key=f"left_{image_key}"
        )

        right = st.slider(
            "오른쪽 (%)",
            10,
            100,
            current_roi["right"],
            key=f"right_{image_key}"
        )

    with col2:

        top = st.slider(
            "위쪽 (%)",
            0,
            90,
            current_roi["top"],
            key=f"top_{image_key}"
        )

        bottom = st.slider(
            "아래쪽 (%)",
            10,
            100,
            current_roi["bottom"],
            key=f"bottom_{image_key}"
        )

    # 좌표 순서 자동 보정
    if left >= right:
        right = min(100, left + 1)

    if top >= bottom:
        bottom = min(100, top + 1)

    # 현재 ROI 저장
    st.session_state.roi_values[image_key] = {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom
    }

    # -----------------------------------------------------
    # ROI 박스가 그려진 사진
    # -----------------------------------------------------

    display_image, coords = make_roi_image(
        image_rgb,
        left,
        right,
        top,
        bottom
    )

    st.subheader("🔲 현재 ROI 영역")

    st.image(
        display_image,
        use_container_width=True
    )

    x1, x2, y1, y2 = coords

    st.caption(
        f"ROI 좌표: x={x1}~{x2}, y={y1}~{y2}"
    )

    # -----------------------------------------------------
    # ROI 분석
    # -----------------------------------------------------

    analysis = analyze_roi(
        image_rgb,
        left,
        right,
        top,
        bottom
    )

    if analysis:

        st.subheader("📊 현재 ROI 분석 결과")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "평균 녹색 밝기",
                f"{analysis['평균 녹색 밝기']:.2f}"
            )

        with c2:
            st.metric(
                "최대 녹색 밝기",
                analysis["최대 녹색 밝기"]
            )

        with c3:
            st.metric(
                "포화 비율",
                f"{analysis['포화 비율(%)']:.2f}%"
            )

    # -----------------------------------------------------
    # 시료 정보 입력
    # -----------------------------------------------------

    st.subheader("🧪 시료 정보")

    if sample_type == "농도 예비실험":

        c1, c2 = st.columns(2)

        with c1:
            concentration = st.number_input(
                "플루오레세인 나트륨 농도 (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.001,
                step=0.001,
                format="%.4f"
            )

        with c2:
            ph_value = st.number_input(
                "pH",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1
            )

        addition_type = ""
        addition_step = ""
        addition_volume = 0.0

    elif sample_type == "pH-형광 기준 시료":

        c1, c2 = st.columns(2)

        with c1:
            ph_value = st.number_input(
                "pH",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1
            )

        with c2:
            concentration = st.number_input(
                "플루오레세인 나트륨 농도 (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.001,
                step=0.001,
                format="%.4f"
            )

        addition_type = ""
        addition_step = ""
        addition_volume = 0.0

    elif sample_type == "pH 6 완충용액":

        c1, c2 = st.columns(2)

        with c1:

            addition_type = st.selectbox(
                "첨가 물질",
                ["없음", "HCl", "NaOH"]
            )

        with c2:

            addition_volume = st.number_input(
                "첨가량 (mL)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=1.0
            )

        c3, c4 = st.columns(2)

        with c3:

            ph_value = st.number_input(
                "측정 pH",
                min_value=0.0,
                max_value=14.0,
                value=6.0,
                step=0.1
            )

        with c4:

            concentration = st.number_input(
                "플루오레세인 나트륨 농도 (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.001,
                step=0.001,
                format="%.4f"
            )

        if addition_type == "없음":
            addition_step = "무첨가"
        else:
            addition_step = f"{addition_volume:g} mL"

    else:

        c1, c2 = st.columns(2)

        with c1:
            ph_value = st.number_input(
                "pH",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1
            )

        with c2:
            concentration = st.number_input(
                "농도 (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.001,
                step=0.001,
                format="%.4f"
            )

        addition_type = ""
        addition_step = ""
        addition_volume = 0.0

    # -----------------------------------------------------
    # 결과 저장
    # -----------------------------------------------------

    st.markdown("---")

    if st.button(
        "💾 현재 사진의 분석 결과 저장",
        type="primary",
        use_container_width=True
    ):

        if analysis:

            st.session_state.results[image_key] = {
                "파일명": selected_file.name,
                "시료 종류": sample_type,
                "첨가 종류": addition_type,
                "첨가 단계": addition_step,
                "첨가량(mL)": addition_volume,
                "농도(%)": concentration,
                "pH": ph_value,
                "평균 녹색 밝기": analysis["평균 녹색 밝기"],
                "최대 녹색 밝기": analysis["최대 녹색 밝기"],
                "포화 비율(%)": analysis["포화 비율(%)"],
                "ROI 왼쪽(%)": left,
                "ROI 오른쪽(%)": right,
                "ROI 위쪽(%)": top,
                "ROI 아래쪽(%)": bottom
            }

            st.success(
                f"'{selected_file.name}' 분석 결과가 저장되었습니다."
            )

    # -----------------------------------------------------
    # 현재 저장 결과
    # -----------------------------------------------------

    if image_key in st.session_state.results:

        st.success("✅ 이 사진의 결과가 저장되어 있습니다.")


# =========================================================
# 전체 데이터
# =========================================================

if st.session_state.results:

    st.markdown("---")
    st.header("📋 저장된 분석 결과")

    df = pd.DataFrame(
        list(st.session_state.results.values())
    )

    df = get_numeric_pH(df)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # CSV 다운로드
    # -----------------------------------------------------

    csv_data = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        "⬇️ CSV 파일 다운로드",
        data=csv_data,
        file_name="fluorescence_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )


    # =====================================================
    # 그래프
    # =====================================================

    st.markdown("---")
    st.header("📈 결과 그래프")


    # =====================================================
    # 1. 농도 예비실험
    # =====================================================

    concentration_df = df[
        df["시료 종류"] == "농도 예비실험"
    ].copy()

    if not concentration_df.empty:

        st.subheader("① 플루오레세인 나트륨 농도에 따른 형광 밝기")

        concentration_df = (
            concentration_df
            .dropna(subset=["농도(%)"])
            .sort_values("농도(%)")
        )

        if len(concentration_df) > 0:

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                concentration_df["농도(%)"],
                concentration_df["평균 녹색 밝기"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "플루오레세인 나트륨 농도 (%)",
                fontsize=12
            )

            ax.set_ylabel(
                "평균 녹색 밝기",
                fontsize=12
            )

            ax.set_title(
                "플루오레세인 나트륨 농도와 형광 밝기의 관계",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


    # =====================================================
    # 2. pH 기준 시료
    # =====================================================

    ph_df = df[
        df["시료 종류"] == "pH-형광 기준 시료"
    ].copy()

    if not ph_df.empty:

        st.subheader("② pH에 따른 플루오레세인 형광 밝기")

        ph_df = (
            ph_df
            .dropna(subset=["pH"])
            .sort_values("pH")
        )

        if len(ph_df) > 0:

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                ph_df["pH"],
                ph_df["평균 녹색 밝기"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "pH",
                fontsize=12
            )

            ax.set_ylabel(
                "평균 녹색 밝기",
                fontsize=12
            )

            ax.set_title(
                "pH와 플루오레세인 형광 밝기의 관계",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


    # =====================================================
    # 3. HCl - pH
    # =====================================================

    buffer_df = df[
        df["시료 종류"] == "pH 6 완충용액"
    ].copy()

    if not buffer_df.empty:

        hcl_df = buffer_df[
            buffer_df["첨가 종류"] == "HCl"
        ].copy()

        naoh_df = buffer_df[
            buffer_df["첨가 종류"] == "NaOH"
        ].copy()


        # -------------------------------------------------
        # HCl 첨가량 - pH
        # -------------------------------------------------

        if not hcl_df.empty:

            st.subheader("③ HCl 첨가량에 따른 pH 변화")

            hcl_df = (
                hcl_df
                .dropna(subset=["첨가량(mL)", "pH"])
                .sort_values("첨가량(mL)")
            )

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                hcl_df["첨가량(mL)"],
                hcl_df["pH"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "HCl 첨가량 (mL)",
                fontsize=12
            )

            ax.set_ylabel(
                "pH",
                fontsize=12
            )

            ax.set_title(
                "HCl 첨가량에 따른 완충용액의 pH 변화",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


        # -------------------------------------------------
        # HCl 첨가량 - 형광
        # -------------------------------------------------

        if not hcl_df.empty:

            st.subheader("④ HCl 첨가량에 따른 형광 밝기 변화")

            hcl_df = hcl_df.sort_values("첨가량(mL)")

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                hcl_df["첨가량(mL)"],
                hcl_df["평균 녹색 밝기"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "HCl 첨가량 (mL)",
                fontsize=12
            )

            ax.set_ylabel(
                "평균 녹색 밝기",
                fontsize=12
            )

            ax.set_title(
                "HCl 첨가량에 따른 형광 밝기 변화",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


        # -------------------------------------------------
        # NaOH - pH
        # -------------------------------------------------

        if not naoh_df.empty:

            st.subheader("⑤ NaOH 첨가량에 따른 pH 변화")

            naoh_df = (
                naoh_df
                .dropna(subset=["첨가량(mL)", "pH"])
                .sort_values("첨가량(mL)")
            )

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                naoh_df["첨가량(mL)"],
                naoh_df["pH"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "NaOH 첨가량 (mL)",
                fontsize=12
            )

            ax.set_ylabel(
                "pH",
                fontsize=12
            )

            ax.set_title(
                "NaOH 첨가량에 따른 완충용액의 pH 변화",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


        # -------------------------------------------------
        # NaOH - 형광
        # -------------------------------------------------

        if not naoh_df.empty:

            st.subheader("⑥ NaOH 첨가량에 따른 형광 밝기 변화")

            naoh_df = naoh_df.sort_values("첨가량(mL)")

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                naoh_df["첨가량(mL)"],
                naoh_df["평균 녹색 밝기"],
                marker="o",
                linewidth=2
            )

            ax.set_xlabel(
                "NaOH 첨가량 (mL)",
                fontsize=12
            )

            ax.set_ylabel(
                "평균 녹색 밝기",
                fontsize=12
            )

            ax.set_title(
                "NaOH 첨가량에 따른 형광 밝기 변화",
                fontsize=14
            )

            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


        # =================================================
        # ⑦ 완충용액 pH - 형광
        # =================================================

        st.subheader("⑦ 완충용액의 pH와 형광 밝기의 관계")

        if not hcl_df.empty:

            hcl_plot = (
                hcl_df
                .dropna(subset=["pH"])
                .sort_values("pH")
            )

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                hcl_plot["pH"],
                hcl_plot["평균 녹색 밝기"],
                marker="o",
                linewidth=2,
                label="HCl 첨가"
            )

            if not naoh_df.empty:

                naoh_plot = (
                    naoh_df
                    .dropna(subset=["pH"])
                    .sort_values("pH")
                )

                ax.plot(
                    naoh_plot["pH"],
                    naoh_plot["평균 녹색 밝기"],
                    marker="o",
                    linewidth=2,
                    label="NaOH 첨가"
                )

            ax.set_xlabel(
                "pH",
                fontsize=12
            )

            ax.set_ylabel(
                "평균 녹색 밝기",
                fontsize=12
            )

            ax.set_title(
                "완충용액의 pH에 따른 플루오레세인 형광 밝기",
                fontsize=14
            )

            ax.legend()
            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            st.pyplot(fig, use_container_width=True)

            plt.close(fig)


# =========================================================
# 안내
# =========================================================

else:

    st.info(
        "사진을 업로드하면 사진별 ROI를 설정하고 분석할 수 있습니다."
    )

    st.markdown(
        """
### 사용 방법

1. 사진을 여러 장 업로드
2. 위의 **분석할 사진 선택**에서 사진 하나 선택
3. 사진 위에 표시되는 **파란색 ROI 박스** 확인
4. 왼쪽·오른쪽·위쪽·아래쪽 슬라이더로 ROI 조절
5. 박스가 **용액 내부의 균일한 부분**을 포함하도록 설정
6. 시료 정보를 입력
7. **현재 사진의 분석 결과 저장** 클릭
8. 다음 사진을 선택하여 같은 방법으로 반복
9. 모든 사진을 저장하면 아래에서 표와 그래프 확인
        """
    )
