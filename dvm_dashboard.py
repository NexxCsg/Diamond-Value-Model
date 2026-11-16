
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Interactive Dashboard - v0.3
# Player Comparison Engine
# ==========================================

DATA_FILE = "dvm_2025_LAD_financial_model.csv"

st.set_page_config(
    page_title="Diamond Value Model",
    page_icon="⚾",
    layout="wide"
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    required = [
        "Name",
        "Total_bWAR",
        "Base_Market_Value",
        "AAV",
        "Base_Salary",
        "Reported_Salary",
        "AAV_Surplus",
        "Salary_Surplus"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df["Name"].duplicated().any():
        raise ValueError(
            "Duplicate player names found. "
            "Comparison requires unique player selections."
        )

    return df


def money(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def number(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


df = load_data()
players = sorted(df["Name"].dropna().unique())

st.title("⚾ Diamond Value Model")
st.caption(
    "DVM v0.3 | Los Angeles Dodgers | 2025 Season"
)

st.info(
    "Prototype valuation: $8 million per bWAR. "
    "This is an illustrative assumption, not a "
    "validated market price. Reported salary, "
    "contract AAV, and base salary are separate metrics."
)

# ==========================================
# NAVIGATION
# ==========================================

page = st.sidebar.radio(
    "Navigation",
    [
        "Team Overview",
        "Player Comparison",
        "Individual Player",
        "Complete Dataset"
    ]
)

st.sidebar.divider()
st.sidebar.caption(
    "DVM | Diamond Value Model"
)

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
        "Total bWAR",
        f"{df['Total_bWAR'].sum():.2f}"
    )

    st.divider()

    top = df.sort_values(
        "Total_bWAR",
        ascending=False
    ).head(15)

    fig = px.bar(
        top,
        x="Name",
        y="Total_bWAR",
        color="Total_bWAR",
        title="Top 15 Dodgers by 2025 bWAR",
        labels={
            "Name": "Player",
            "Total_bWAR": "Baseball-Reference WAR"
        }
    )

    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("Contract Value Comparison")

    financial = df[df["AAV"].notna()].copy()

    if not financial.empty:

        financial["Market Value ($M)"] = (
            financial["Base_Market_Value"] / 1e6
        )

        financial["AAV ($M)"] = (
            financial["AAV"] / 1e6
        )

        fig2 = px.bar(
            financial,
            x="Name",
            y=["Market Value ($M)", "AAV ($M)"],
            barmode="group",
            title="Estimated Market Value vs Contract AAV"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        financial["Surplus ($M)"] = (
            financial["AAV_Surplus"] / 1e6
        )

        fig3 = px.bar(
            financial,
            x="Name",
            y="Surplus ($M)",
            title="Historical AAV Economic Surplus"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

# ==========================================
# PLAYER COMPARISON ENGINE
# ==========================================

elif page == "Player Comparison":

    st.header("Player Comparison Engine")

    st.write(
        "Select two players to compare their "
        "2025 performance and financial valuations."
    )

    default_a = (
        players.index("Shohei Ohtani")
        if "Shohei Ohtani" in players else 0
    )

    default_b = (
        players.index("Mookie Betts")
        if "Mookie Betts" in players else min(1, len(players) - 1)
    )

    left, right = st.columns(2)

    with left:
        player_a = st.selectbox(
            "Player A",
            players,
            index=default_a
        )

    with right:
        player_b = st.selectbox(
            "Player B",
            players,
            index=default_b
        )

    if player_a == player_b:
        st.warning(
            "Select two different players to compare."
        )
    else:

        a = df[df["Name"] == player_a].iloc[0]
        b = df[df["Name"] == player_b].iloc[0]

        st.divider()

        st.subheader("Side-by-Side Comparison")

        metrics = [
            ("2025 bWAR", "Total_bWAR", number),
            ("Estimated Market Value", "Base_Market_Value", money),
            ("Reported Salary", "Reported_Salary", money),
            ("Contract AAV", "AAV", money),
            ("Base Salary", "Base_Salary", money),
            ("AAV Economic Surplus", "AAV_Surplus", money),
            ("Base Salary Surplus", "Salary_Surplus", money)
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

        st.divider()

        st.subheader("WAR Comparison")

        war_chart = pd.DataFrame({
            "Player": [player_a, player_b],
            "bWAR": [
                a["Total_bWAR"],
                b["Total_bWAR"]
            ]
        })

        fig_war = px.bar(
            war_chart,
            x="Player",
            y="bWAR",
            color="Player",
            title="2025 Baseball-Reference WAR"
        )

        st.plotly_chart(
            fig_war,
            use_container_width=True
        )

        st.subheader("Financial Value Comparison")

        financial_rows = []

        for name, record in [
            (player_a, a),
            (player_b, b)
        ]:
            for label, column in [
                ("Estimated Market Value", "Base_Market_Value"),
                ("Contract AAV", "AAV"),
                ("Reported Salary", "Reported_Salary")
            ]:
                value = record[column]

                if pd.notna(value):
                    financial_rows.append({
                        "Player": name,
                        "Metric": label,
                        "USD Millions": value / 1e6
                    })

        if financial_rows:

            fig_money = px.bar(
                pd.DataFrame(financial_rows),
                x="Player",
                y="USD Millions",
                color="Metric",
                barmode="group",
                title="Financial Metrics by Player"
            )

            st.plotly_chart(
                fig_money,
                use_container_width=True
            )

        st.subheader("Economic Surplus")

        surplus_rows = []

        for name, record in [
            (player_a, a),
            (player_b, b)
        ]:
            value = record["AAV_Surplus"]

            if pd.notna(value):
                surplus_rows.append({
                    "Player": name,
                    "AAV Surplus ($M)": value / 1e6
                })

        if surplus_rows:

            fig_surplus = px.bar(
                pd.DataFrame(surplus_rows),
                x="Player",
                y="AAV Surplus ($M)",
                color="Player",
                title="Historical AAV Economic Surplus"
            )

            fig_surplus.add_hline(
                y=0,
                line_dash="dash"
            )

            st.plotly_chart(
                fig_surplus,
                use_container_width=True
            )

        else:
            st.info(
                "Neither player has contractual AAV "
                "data available for surplus comparison."
            )

        st.caption(
            "AAV surplus = estimated historical market "
            "value minus nominal contractual AAV. "
            "It is not a forecast of future value. "
            "Missing contract information is not "
            "treated as zero."
        )

# ==========================================
# INDIVIDUAL PLAYER
# ==========================================

elif page == "Individual Player":

    st.header("Individual Player Analysis")

    player = st.selectbox(
        "Select Player",
        players
    )

    record = df[df["Name"] == player].iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "2025 bWAR",
        number(record["Total_bWAR"])
    )

    c2.metric(
        "Estimated Market Value",
        money(record["Base_Market_Value"])
    )

    c3.metric(
        "Reported Salary",
        money(record["Reported_Salary"])
    )

    st.divider()

    st.subheader("Contract Analysis")

    st.write(
        "**Contract AAV:**",
        money(record["AAV"])
    )

    st.write(
        "**Base Salary:**",
        money(record["Base_Salary"])
    )

    st.write(
        "**AAV Economic Surplus:**",
        money(record["AAV_Surplus"])
    )

    st.write(
        "**Base Salary Surplus:**",
        money(record["Salary_Surplus"])
    )

    st.caption(
        "Unavailable financial fields indicate "
        "missing source data, not a zero-dollar contract."
    )

# ==========================================
# COMPLETE DATASET
# ==========================================

elif page == "Complete Dataset":

    st.header("Complete DVM Dataset")

    columns = [
        "Name",
        "Total_bWAR",
        "Base_Market_Value",
        "Reported_Salary",
        "AAV",
        "Base_Salary",
        "AAV_Surplus",
        "Salary_Surplus"
    ]

    st.dataframe(
        df[columns].sort_values(
            "Total_bWAR",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    csv = df.to_csv(index=False)

    st.download_button(
        "Download DVM Dataset",
        data=csv,
        file_name="DVM_2025_Dodgers.csv",
        mime="text/csv"
    )

st.divider()

st.caption(
    "Diamond Value Model | Development Prototype v0.3"
)
