
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# DIAMOND VALUE MODEL
# 2026 Backtesting Dashboard - v0.4
# ==========================================

BACKTEST_FILE = "dvm_2026_backtest.csv"
BASELINE_FILE = "dvm_2026_baseline_comparison.csv"

st.set_page_config(
    page_title="DVM | 2026 Backtest",
    page_icon="⚾",
    layout="wide"
)


@st.cache_data
def load_data():
    backtest = pd.read_csv(BACKTEST_FILE)
    baselines = pd.read_csv(BASELINE_FILE)

    required = [
        "Name", "Projected_bWAR",
        "Actual_2026_bWAR", "Error_WAR",
        "Absolute_Error_WAR"
    ]

    missing = [
        c for c in required
        if c not in backtest.columns
    ]

    if missing:
        raise ValueError(
            f"Missing backtest columns: {missing}"
        )

    return backtest, baselines


backtest, baselines = load_data()

evaluated = backtest.dropna(
    subset=["Projected_bWAR", "Actual_2026_bWAR"]
).copy()

st.title("⚾ DVM | 2026 Backtesting")
st.caption(
    "2025 Dodgers cohort | 2026 actual performance"
)

st.warning(
    "Retrospective diagnostic only. The age-curve "
    "model was created after the 2026 season, "
    "so these results are not an independent "
    "preseason forecasting track record."
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Players Projected", len(backtest))
c2.metric("Players Evaluated", len(evaluated))
c3.metric(
    "Mean Absolute Error",
    f"{evaluated['Absolute_Error_WAR'].mean():.3f}"
)
c4.metric(
    "Mean Bias",
    f"{evaluated['Error_WAR'].mean():+.3f}"
)

st.divider()

st.header("Model Comparison")

fig_baselines = px.bar(
    baselines.sort_values("MAE"),
    x="Model",
    y="MAE",
    color="Model",
    title="Mean Absolute Error — Lower Is Better"
)

st.plotly_chart(
    fig_baselines,
    use_container_width=True
)

st.dataframe(
    baselines,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.header("Projected vs Actual WAR")

fig_scatter = px.scatter(
    evaluated,
    x="Projected_bWAR",
    y="Actual_2026_bWAR",
    hover_name="Name",
    title="2026 Projected vs Actual bWAR",
    labels={
        "Projected_bWAR": "DVM Projected WAR",
        "Actual_2026_bWAR": "Actual 2026 WAR"
    }
)

low = min(
    evaluated["Projected_bWAR"].min(),
    evaluated["Actual_2026_bWAR"].min()
)

high = max(
    evaluated["Projected_bWAR"].max(),
    evaluated["Actual_2026_bWAR"].max()
)

fig_scatter.add_shape(
    type="line",
    x0=low,
    y0=low,
    x1=high,
    y1=high,
    line=dict(
        color="gray",
        dash="dash"
    )
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)

st.caption(
    "Points near the diagonal indicate more "
    "accurate predictions."
)

st.divider()

st.header("Largest Projection Errors")

largest = evaluated.nlargest(
    15, "Absolute_Error_WAR"
)

fig_errors = px.bar(
    largest,
    x="Name",
    y="Error_WAR",
    color="Error_WAR",
    title="Largest 2026 Projection Misses",
    labels={
        "Error_WAR": "Actual minus Projected WAR"
    }
)

fig_errors.add_hline(y=0, line_dash="dash")

st.plotly_chart(
    fig_errors,
    use_container_width=True
)

st.divider()

st.header("Individual Player Backtest")

player = st.selectbox(
    "Select Player",
    sorted(evaluated["Name"].unique())
)

record = evaluated[
    evaluated["Name"] == player
].iloc[0]

a, b, c = st.columns(3)

a.metric(
    "Projected 2026 WAR",
    f"{record['Projected_bWAR']:.3f}"
)

b.metric(
    "Actual 2026 WAR",
    f"{record['Actual_2026_bWAR']:.3f}"
)

c.metric(
    "Prediction Error",
    f"{record['Error_WAR']:+.3f}"
)

st.divider()

st.header("Complete Backtest Results")

st.dataframe(
    backtest[
        [
            "Name",
            "Historical_bWAR",
            "Projected_bWAR",
            "Actual_2026_bWAR",
            "Error_WAR",
            "Absolute_Error_WAR"
        ]
    ].sort_values(
        "Absolute_Error_WAR",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Backtest Results",
    data=backtest.to_csv(index=False),
    file_name="DVM_2026_Backtest.csv",
    mime="text/csv"
)

st.caption(
    "14 players without matched 2026 WAR records "
    "are excluded from accuracy calculations."
)
