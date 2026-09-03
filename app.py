# =========================================================
# 그래프
# =========================================================

st.divider()
st.header("📈 실험 결과 그래프")


# ---------------------------------------------------------
# 완충용액 데이터
# ---------------------------------------------------------

buffer = df[
    df["시료 종류"] == "pH 6 완충용액"
].copy()

buffer["pH"] = pd.to_numeric(buffer["pH"], errors="coerce")
buffer["첨가량(mL)"] = pd.to_numeric(buffer["첨가량(mL)"], errors="coerce")
buffer["평균 녹색 밝기"] = pd.to_numeric(
    buffer["평균 녹색 밝기"],
    errors="coerce"
)


# ---------------------------------------------------------
# HCl 데이터
# ---------------------------------------------------------

hcl = buffer[
    buffer["첨가 종류"] == "HCl"
].dropna(
    subset=["첨가량(mL)", "pH", "평균 녹색 밝기"]
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

    # ① HCl 첨가량 - pH
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
        xaxis=dict(dtick=1)
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )


    # ② HCl 첨가량 - 형광
    st.subheader("② HCl 첨가량에 따른 형광 밝기 변화")

    fig2 = px.line(
        hcl,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "HCl 첨가량 (mL)",
            "평균 녹색 밝기": "평균 녹색 밝기"
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
# NaOH 데이터
# ---------------------------------------------------------

naoh = buffer[
    buffer["첨가 종류"] == "NaOH"
].dropna(
    subset=["첨가량(mL)", "pH", "평균 녹색 밝기"]
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

    # ③ NaOH 첨가량 - pH
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


    # ④ NaOH 첨가량 - 형광
    st.subheader("④ NaOH 첨가량에 따른 형광 밝기 변화")

    fig4 = px.line(
        naoh,
        x="첨가량(mL)",
        y="평균 녹색 밝기",
        markers=True,
        labels={
            "첨가량(mL)": "NaOH 첨가량 (mL)",
            "평균 녹색 밝기": "평균 녹색 밝기"
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
# ⑤ pH - 형광 밝기
# ---------------------------------------------------------

if len(buffer) > 0:

    graph_buffer = buffer.dropna(
        subset=["pH", "평균 녹색 밝기"]
    ).copy()

    if len(graph_buffer) > 0:

        st.subheader("⑤ pH 변화에 따른 완충용액의 형광 밝기")

        fig5 = px.scatter(
            graph_buffer,
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

        fig5.update_layout(
            height=500
        )

        st.plotly_chart(
            fig5,
            use_container_width=True
        )
