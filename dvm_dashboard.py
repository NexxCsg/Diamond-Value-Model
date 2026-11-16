
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Interactive Dashboard - v0.4
# Age-Adjusted WAR Projections
# ==========================================

DATA_FILE = "dvm_2025_LAD_financial_model.csv"
AGE_FILE = "dvm_2025_LAD_with_ages.csv"
PROJECTION_FILE = "dvm_2025_LAD_age_projections.csv"

st.set_page_config(
    page_title="Diamond Value Model",
    page_icon="⚾",
    layout="wide"
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    ages = pd.read_csv(AGE_FILE)
    projections = pd.read_csv(PROJECTION_FILE)

    required = [
        "MLBAM_ID", "Name", "Total_bWAR",
        "Base_Market_Value", "AAV",
        "Base_Salary", "Reported_Salary",
        "AAV_Surplus", "Salary_Surplus"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing financial columns: {missing}")

    if df["MLBAM_ID"].duplicated().any():
        raise ValueError("Duplicate player IDs in financial data")

    if ages["MLBAM_ID"].duplicated().any():
        raise ValueError("Duplicate player IDs in age data")

    if projections.duplicated(
        ["MLBAM_ID", "Projection_Year"]
    ).any():
        raise ValueError("Duplicate projection records")

    df = df.merge(
        ages[["MLBAM_ID", "Age"]],
        on="MLBAM_ID",
        how="left",
        validate="one_to_one"
    )

    return df, projections


def money(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def number(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


df, projections = load_data()

players = sorted(df["Name"].dropna().unique())

st.title("⚾ Diamond Value Model")
st.caption("DVM v0.4 | 2025 Los Angeles Dodgers")

st.info(
    "Development prototype. Historical valuations use "
    "an illustrative $8 million per bWAR. Future WAR "
    "projections use an uncalibrated age curve, not "
    "a statistically validated forecasting model."
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Team Overview",
        "Player Comparison",
        "Age Projections",
        "Individual Player",
        "Complete Dataset"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Diamond Value Model | v0.4")

# ==========================================
# TEAM OVERVIEW
# ==========================================

if page == "Team Overview":

    st.header("2025 Dodgers Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Players", len(df))
    c2.metric(
        "Reported Salaries",
        int(df["Reported_Salary"].notna().sum())
    )
    c3.metric(
        "Contract Records",
        int(df["AAV"].notna().sum())
    )
    c4.metric(
        "Total Historical bWAR",
        number(df["Total_bWAR"].sum())
    )

    top = df.nlargest(15, "Total_bWAR")

    fig = px.bar(
        top,
        x="Name",
        y="Total_bWAR",
        color="Total_bWAR",
        title="Top 15 Dodgers by 2025 bWAR"
    )

    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Historical Financial Valuation")

    financial = df[df["AAV"].notna()].copy()

    if not financial.empty:
        financial["Market Value ($M)"] = (
            financial["Base_Market_Value"] / 1e6
        )
        financial["AAV ($M)"] = financial["AAV"] / 1e6
        financial["Surplus ($M)"] = (
            financial["AAV_Surplus"] / 1e6
        )

        fig2 = px.bar(
            financial,
            x="Name",
            y=["Market Value ($M)", "AAV ($M)"],
            barmode="group",
            title="Historical Market Value vs AAV"
        )

        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.bar(
            financial,
            x="Name",
            y="Surplus ($M)",
            title="Historical AAV Economic Surplus"
        )

        fig3.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# PLAYER COMPARISON
# ==========================================

elif page == "Player Comparison":

    st.header("Player Comparison Engine")

    default_a = (
        players.index("Shohei Ohtani")
        if "Shohei Ohtani" in players else 0
    )
    default_b = (
        players.index("Mookie Betts")
        if "Mookie Betts" in players else min(1, len(players) - 1)
    )

    c1, c2 = st.columns(2)

    with c1:
        player_a = st.selectbox(
            "Player A", players, index=default_a
        )

    with c2:
        player_b = st.selectbox(
            "Player B", players, index=default_b
        )

    if player_a == player_b:
        st.warning("Select two different players.")
    else:
        a = df[df["Name"] == player_a].iloc[0]
        b = df[df["Name"] == player_b].iloc[0]

        metrics = [
            ("Age", "Age", number),
            ("2025 bWAR", "Total_bWAR", number),
            ("Estimated Market Value", "Base_Market_Value", money),
            ("Reported Salary", "Reported_Salary", money),
            ("Contract AAV", "AAV", money),
            ("Base Salary", "Base_Salary", money),
            ("AAV Surplus", "AAV_Surplus", money),
            ("Salary Surplus", "Salary_Surplus", money)
        ]

        comparison = []

        for label, column, formatter in metrics:
            comparison.append({
                "Metric": label,
                player_a: formatter(a[column]),
                player_b: formatter(b[column])
            })

        st.dataframe(
            pd.DataFrame(comparison).set_index("Metric"),
            use_container_width=True
        )

        war_data = pd.DataFrame({
            "Player": [player_a, player_b],
            "bWAR": [a["Total_bWAR"], b["Total_bWAR"]]
        })

        st.plotly_chart(
            px.bar(
                war_data,
                x="Player",
                y="bWAR",
                color="Player",
                title="Historical WAR Comparison"
            ),
            use_container_width=True
        )

        financial_rows = []

        for name, record in [(player_a, a), (player_b, b)]:
            for label, column in [
                ("Market Value", "Base_Market_Value"),
                ("Contract AAV", "AAV"),
                ("Reported Salary", "Reported_Salary")
            ]:
                if pd.notna(record[column]):
                    financial_rows.append({
                        "Player": name,
                        "Metric": label,
                        "USD Millions": record[column] / 1e6
                    })

        if financial_rows:
            st.plotly_chart(
                px.bar(
                    pd.DataFrame(financial_rows),
                    x="Player",
                    y="USD Millions",
                    color="Metric",
                    barmode="group",
                    title="Financial Comparison"
                ),
                use_container_width=True
            )

        surplus_rows = []

        for name, record in [(player_a, a), (player_b, b)]:
            if pd.notna(record["AAV_Surplus"]):
                surplus_rows.append({
                    "Player": name,
                    "Surplus ($M)": record["AAV_Surplus"] / 1e6
                })

        if surplus_rows:
            fig = px.bar(
                pd.DataFrame(surplus_rows),
                x="Player",
                y="Surplus ($M)",
                color="Player",
                title="Historical AAV Economic Surplus"
            )
            fig.add_hline(y=0, line_dash="dash")
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# AGE PROJECTIONS - NEW IN v0.4
# ==========================================

elif page == "Age Projections":

    st.header("Age-Adjusted WAR Projections")
    st.caption("Experimental projections for 2026–2028")

    default = [
        name for name in [
            "Shohei Ohtani",
            "Mookie Betts",
            "Yoshinobu Yamamoto",
            "Andy Pages"
        ]
        if name in players
    ]

    selected = st.multiselect(
        "Select Players",
        players,
        default=default
    )

    if not selected:
        st.warning("Select at least one player.")
    else:
        selected_ids = df.loc[
            df["Name"].isin(selected), "MLBAM_ID"
        ]

        future = projections[
            projections["MLBAM_ID"].isin(selected_ids)
        ].copy()

        historical = df[
            df["MLBAM_ID"].isin(selected_ids)
        ][["MLBAM_ID", "Name", "Total_bWAR"]].copy()

        historical["Projection_Year"] = 2025
        historical["Projected_bWAR"] = (
            historical["Total_bWAR"]
        )
        historical["Series"] = "Historical"

        future["Series"] = "Projected"

        chart_data = pd.concat(
            [
                historical[
                    [
                        "MLBAM_ID", "Name",
                        "Projection_Year",
                        "Projected_bWAR", "Series"
                    ]
                ],
                future[
                    [
                        "MLBAM_ID", "Name",
                        "Projection_Year",
                        "Projected_bWAR", "Series"
                    ]
                ]
            ],
            ignore_index=True
        )

        fig = px.line(
            chart_data,
            x="Projection_Year",
            y="Projected_bWAR",
            color="Name",
            markers=True,
            title="Historical and Projected WAR",
            labels={
                "Projection_Year": "Season",
                "Projected_bWAR": "bWAR",
                "Name": "Player"
            },
            hover_data=["Series"]
        )

        fig.update_xaxes(
            tickmode="array",
            tickvals=[2025, 2026, 2027, 2028]
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "2025 is observed bWAR. 2026–2028 are "
            "illustrative model outputs, not observed "
            "performance. Negative historical WAR is "
            "floored at zero for the projection baseline."
        )

        st.subheader("Projected Market Value")

        future["Market Value ($M)"] = (
            future["Projected_Market_Value"] / 1e6
        )

        fig_value = px.bar(
            future,
            x="Projection_Year",
            y="Market Value ($M)",
            color="Name",
            barmode="group",
            title="Projected Annual Market Value",
            labels={
                "Projection_Year": "Season",
                "Name": "Player"
            }
        )

        fig_value.update_xaxes(
            tickmode="array",
            tickvals=[2026, 2027, 2028]
        )

        st.plotly_chart(
            fig_value,
            use_container_width=True
        )

        st.subheader("Projection Data")

        st.dataframe(
            future[
                [
                    "Name",
                    "Projection_Year",
                    "Projected_Age",
                    "Age_Multiplier",
                    "Projected_bWAR",
                    "Projected_Market_Value"
                ]
            ].sort_values(
                ["Name", "Projection_Year"]
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("2026 Projected WAR Leaderboard")

    leaderboard = projections[
        projections["Projection_Year"] == 2026
    ].nlargest(15, "Projected_bWAR")

    st.plotly_chart(
        px.bar(
            leaderboard,
            x="Name",
            y="Projected_bWAR",
            color="Projected_bWAR",
            title="Top 15 Players — 2026 Projection"
        ),
        use_container_width=True
    )

# ==========================================
# INDIVIDUAL PLAYER
# ==========================================

elif page == "Individual Player":

    st.header("Individual Player Analysis")

    player = st.selectbox("Select Player", players)
    record = df[df["Name"] == player].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Age in 2025", number(record["Age"]))
    c2.metric("2025 bWAR", number(record["Total_bWAR"]))
    c3.metric(
        "Historical Market Value",
        money(record["Base_Market_Value"])
    )
    c4.metric(
        "Reported Salary",
        money(record["Reported_Salary"])
    )

    st.subheader("Contract Analysis")

    st.write("**Contract AAV:**", money(record["AAV"]))
    st.write("**Base Salary:**", money(record["Base_Salary"]))
    st.write("**AAV Surplus:**", money(record["AAV_Surplus"]))
    st.write(
        "**Salary Surplus:**",
        money(record["Salary_Surplus"])
    )

    st.subheader("Future Age Projections")

    player_projections = projections[
        projections["MLBAM_ID"] == record["MLBAM_ID"]
    ].sort_values("Projection_Year")

    st.dataframe(
        player_projections[
            [
                "Projection_Year",
                "Projected_Age",
                "Projected_bWAR",
                "Projected_Market_Value"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# COMPLETE DATASET
# ==========================================

elif page == "Complete Dataset":

    st.header("Complete DVM Dataset")

    columns = [
        "Name", "Age", "Total_bWAR",
        "Base_Market_Value", "Reported_Salary",
        "AAV", "Base_Salary",
        "AAV_Surplus", "Salary_Surplus"
    ]

    st.dataframe(
        df[columns].sort_values(
            "Total_bWAR",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Financial Dataset",
        data=df.to_csv(index=False),
        file_name="DVM_2025_Dodgers.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download Age Projections",
        data=projections.to_csv(index=False),
        file_name="DVM_Age_Projections.csv",
        mime="text/csv"
    )

st.divider()

st.caption(
    "Diamond Value Model | v0.4 Development Prototype"
)
