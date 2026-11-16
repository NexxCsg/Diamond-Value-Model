
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Interactive Dashboard - v0.2
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
        "Name", "Total_bWAR", "Base_Market_Value",
        "AAV", "Base_Salary", "Reported_Salary",
        "AAV_Surplus", "Salary_Surplus"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df


df = load_data()

st.title("⚾ Diamond Value Model")
st.caption(
    "DVM v0.2 | Los Angeles Dodgers | 2025 Season"
)

st.info(
    "Early prototype: valuations use an illustrative "
    "$8 million per WAR assumption. Contract coverage "
    "and financial methodology are still being developed."
)

# ------------------------------------------
# DASHBOARD METRICS
# ------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Players", len(df))

col2.metric(
    "Reported Salaries",
    int(df["Reported_Salary"].notna().sum())
)

col3.metric(
    "Contract AAV Records",
    int(df["AAV"].notna().sum())
)

col4.metric(
    "Total Team bWAR",
    f"{df['Total_bWAR'].sum():.2f}"
)

st.divider()

# ------------------------------------------
# PLAYER FILTER
# ------------------------------------------

st.sidebar.header("DVM Controls")

selected_players = st.sidebar.multiselect(
    "Select Players",
    options=sorted(df["Name"].unique()),
    default=sorted(df["Name"].unique())
)

filtered = df[
    df["Name"].isin(selected_players)
].copy()

st.subheader("Player Performance")

performance = filtered.sort_values(
    "Total_bWAR",
    ascending=False
)

fig_war = px.bar(
    performance,
    x="Name",
    y="Total_bWAR",
    color="Total_bWAR",
    title="2025 Player bWAR",
    labels={
        "Name": "Player",
        "Total_bWAR": "Baseball-Reference WAR"
    }
)

fig_war.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig_war,
    use_container_width=True
)

# ------------------------------------------
# FINANCIAL COMPARISON
# ------------------------------------------

st.subheader("Financial Comparison")

financial = filtered[
    filtered["AAV"].notna()
].copy()

if not financial.empty:

    financial["AAV_Millions"] = (
        financial["AAV"] / 1_000_000
    )

    financial["Market_Value_Millions"] = (
        financial["Base_Market_Value"] / 1_000_000
    )

    financial["Surplus_Millions"] = (
        financial["AAV_Surplus"] / 1_000_000
    )

    fig_financial = px.bar(
        financial,
        x="Name",
        y=[
            "Market_Value_Millions",
            "AAV_Millions"
        ],
        barmode="group",
        title="Estimated Market Value vs Contract AAV",
        labels={
            "value": "USD Millions",
            "Name": "Player",
            "variable": "Metric"
        }
    )

    st.plotly_chart(
        fig_financial,
        use_container_width=True
    )

    fig_surplus = px.bar(
        financial,
        x="Name",
        y="Surplus_Millions",
        title="Estimated Economic Surplus",
        labels={
            "Surplus_Millions": "USD Millions",
            "Name": "Player"
        }
    )

    st.plotly_chart(
        fig_surplus,
        use_container_width=True
    )

else:
    st.warning(
        "No players with contractual AAV "
        "in the current selection."
    )

# ------------------------------------------
# PLAYER DETAILS
# ------------------------------------------

st.divider()

st.subheader("Individual Player Analysis")

player = st.selectbox(
    "Choose a Player",
    sorted(df["Name"].unique())
)

record = df[df["Name"] == player].iloc[0]


def money(value):
    if pd.isna(value):
        return "Not available"
    return f"${value:,.0f}"


left, middle, right = st.columns(3)

left.metric(
    "2025 bWAR",
    f"{record['Total_bWAR']:.2f}"
)

middle.metric(
    "Estimated Market Value",
    money(record["Base_Market_Value"])
)

right.metric(
    "Reported Salary",
    money(record["Reported_Salary"])
)

st.write("**Contractual AAV:**", money(record["AAV"]))
st.write("**Base Salary:**", money(record["Base_Salary"]))
st.write("**AAV Surplus:**", money(record["AAV_Surplus"]))
st.write(
    "**Salary Surplus:**",
    money(record["Salary_Surplus"])
)

# ------------------------------------------
# DATA TABLE
# ------------------------------------------

st.divider()

st.subheader("Complete DVM Dataset")

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
    filtered[columns].sort_values(
        "Total_bWAR",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Reported salary is not interchangeable "
    "with nominal AAV, contractual base salary, "
    "or actual cash paid. Age and injury-risk "
    "adjustments are planned for future versions."
)
