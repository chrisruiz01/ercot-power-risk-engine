import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9
})

# --- PAGE CONFIG ---
st.set_page_config(page_title="ERCOT Power Price Risk Engine", layout="wide")

# --- LOAD DATA ---
df_temp = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])
merged = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# --- BUILD TEMP → LOAD MODEL ---
df_temp["month"] = df_temp["DATE"].dt.month
df_temp["TMAX_sq"] = df_temp["TMAX"] ** 2

X = df_temp[["TMAX", "TMAX_sq", "month"]]
y = df_temp["daily_peak_load"]

model = LinearRegression()
model.fit(X, y)

def predict_load(temp, month):
    input_df = pd.DataFrame({
        "TMAX": [temp],
        "TMAX_sq": [temp**2],
        "month": [month]
    })
    return model.predict(input_df)[0]

# --- DECISION LOGIC ---
WATCH_THRESHOLD = 0.10
HEDGE_THRESHOLD = 0.17
SPIKE_PRICE_THRESHOLD = 200

def decision(prob):
    if prob >= HEDGE_THRESHOLD:
        return "HEDGE"
    elif prob >= WATCH_THRESHOLD:
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"

# --- BUILD RISK CURVE ---
merged["is_spike"] = merged["price"] > SPIKE_PRICE_THRESHOLD
avg_spike_price = merged.loc[merged["is_spike"], "price"].mean()
avg_normal_price = merged.loc[~merged["is_spike"], "price"].mean()
merged["load_bin"] = pd.cut(merged["ercot_load"], bins=30)

risk_curve = merged.groupby("load_bin", observed=False).agg(
    load_mid=("ercot_load", "mean"),
    spike_prob=("is_spike", "mean"),
    count=("price", "count")
).reset_index()

risk_curve = risk_curve[risk_curve["count"] > 50].copy()
risk_curve = risk_curve.sort_values("load_mid")

load_levels = risk_curve["load_mid"].values
spike_probs = risk_curve["spike_prob"].values

def get_prob(load):
    return float(np.interp(load, load_levels, spike_probs))

def get_load_at_prob(target_prob, spike_probs, load_levels):
    return float(np.interp(target_prob, spike_probs, load_levels))

# --- MONTH MAP ---
month_map = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}
month_names = list(month_map.keys())

# --- PREP HISTORICAL DAILY DATA ---
merged["date"] = merged["timestamp"].dt.date
merged["month"] = merged["timestamp"].dt.month

daily = merged.groupby("date").agg(
    actual_load=("ercot_load", "max"),
    actual_price=("price", "max")
).reset_index()

daily["date"] = pd.to_datetime(daily["date"])
daily["month"] = daily["date"].dt.month
daily["model_spike_probability"] = daily["actual_load"].apply(get_prob)
daily["model_decision"] = daily["model_spike_probability"].apply(decision)
daily["actual_spike"] = daily["actual_price"] > SPIKE_PRICE_THRESHOLD
daily["watch_signal"] = daily["model_spike_probability"] >= WATCH_THRESHOLD
daily["hedge_signal"] = daily["model_spike_probability"] >= HEDGE_THRESHOLD
daily = daily.sort_values("date")

# --- SESSION STATE FOR HISTORICAL DEFAULT ALIGNMENT ---
if "selected_month" not in st.session_state:
    st.session_state.selected_month = 7

if "selected_hist_date" not in st.session_state:
    same_month_dates = daily.loc[daily["month"] == st.session_state.selected_month, "date"]
    if not same_month_dates.empty:
        st.session_state.selected_hist_date = same_month_dates.max().date()
    else:
        st.session_state.selected_hist_date = daily["date"].max().date()

def update_hist_date_to_month_default():
    selected_month = st.session_state.selected_month
    same_month_dates = daily.loc[daily["month"] == selected_month, "date"]
    if not same_month_dates.empty:
        st.session_state.selected_hist_date = same_month_dates.max().date()
    else:
        st.session_state.selected_hist_date = daily["date"].max().date()

# --- UI HEADER ---
st.title("ERCOT Power Price Risk Engine")

caption_col1, caption_col2 = st.columns(2)
with caption_col1:
    st.caption("Simulate future conditions to estimate spike risk based on expected load.")
with caption_col2:
    st.caption("Test model decisions against real historical outcomes.")

with st.expander("What these metrics mean"):
    st.markdown(f"""
- **Predicted Load**: expected ERCOT peak load based on selected temperature and month  
- **Spike Probability**: historical probability of price exceeding **${SPIKE_PRICE_THRESHOLD}/MWh** at similar load levels  
- **WATCH**: conditions are entering a higher-risk zone  
- **HEDGE**: conditions imply materially elevated spike risk  
- **Expected Loss**: spike probability multiplied by the assumed economic price impact  
- **Economic Decision**: compares expected loss against hedge cost  
- **Historical Replay**: shows what the model would have signaled on an actual past day  
- **Important caveat**: this model uses **load** as the main driver of price risk. Actual prices also depend on outages, renewable output, fuel conditions, congestion, and broader scarcity conditions.
    """)

# --- TOP PANELS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Risk")

    temp = st.slider("Temperature (°F)", 80, 105, 97)

    selected_month_name = st.selectbox(
        "Month",
        month_names,
        index=6,
        key="forward_month_name"
    )
    month = month_map[selected_month_name]

    if st.session_state.selected_month != month:
        st.session_state.selected_month = month
        update_hist_date_to_month_default()

    predicted_load = predict_load(temp, month)
    prob = get_prob(predicted_load)
    dec = decision(prob)

    use_empirical = st.checkbox("Use Empirical Prices", value=True)

    if use_empirical:
        normal_price = float(avg_normal_price)
        spike_price = float(avg_spike_price)
    else:
        normal_price = st.number_input("Normal Price ($/MWh)", value=50.0)
        spike_price = st.number_input("Spike Price ($/MWh)", value=500.0)

    hedge_cost = st.number_input("Hedge Cost ($/MWh)", value=20.0)
    expected_loss = prob * (spike_price - normal_price)
    econ_decision = "HEDGE (Economic)" if expected_loss > hedge_cost else "NO HEDGE (Economic)"

    watch_gap = max(0, WATCH_THRESHOLD - prob)
    hedge_gap = max(0, HEDGE_THRESHOLD - prob)

    watch_load = get_load_at_prob(WATCH_THRESHOLD, spike_probs, load_levels)
    hedge_load = get_load_at_prob(HEDGE_THRESHOLD, spike_probs, load_levels)

    watch_load_gap = watch_load - predicted_load
    hedge_load_gap = hedge_load - predicted_load

    st.metric("Predicted Load", f"{int(predicted_load):,}")
    st.metric("Spike Probability", f"{prob:.3f}")
    st.metric("Expected Spike Cost ($/MWh)", f"{expected_loss:.2f}")

    gap_col1, gap_col2 = st.columns(2)
    with gap_col1:
        st.metric("Gap to WATCH", f"{watch_gap:.3f}")
        st.metric("Load Gap to WATCH", f"{int(watch_load_gap):,}")
    with gap_col2:
        st.metric("Gap to HEDGE", f"{hedge_gap:.3f}")
        st.metric("Load Gap to HEDGE", f"{int(hedge_load_gap):,}")

    if dec == "HEDGE":
        st.error(f"Decision: {dec}")
    elif dec == "WATCH / PARTIAL HEDGE":
        st.warning(f"Decision: {dec}")
    else:
        st.success(f"Decision: {dec}")

    st.info(econ_decision)

# --- ECONOMIC BACKTEST COLUMNS ---
daily["expected_loss"] = daily["model_spike_probability"] * (spike_price - normal_price)
daily["economic_decision"] = np.where(daily["expected_loss"] > hedge_cost, "HEDGE", "NO HEDGE")
daily["no_hedge_cost"] = daily["actual_price"]
daily["hedged_cost"] = normal_price + hedge_cost
daily["strategy_cost"] = np.where(
    daily["economic_decision"] == "HEDGE",
    daily["hedged_cost"],
    daily["no_hedge_cost"]
)
daily["savings_vs_no_hedge"] = daily["no_hedge_cost"] - daily["strategy_cost"]

with col2:
    st.subheader("Historical Replay")

    date_options = daily["date"].dt.date.tolist()

    if st.session_state.selected_hist_date not in date_options:
        same_month_dates = daily.loc[daily["month"] == month, "date"]
        if not same_month_dates.empty:
            st.session_state.selected_hist_date = same_month_dates.max().date()
        else:
            st.session_state.selected_hist_date = daily["date"].max().date()

    selected_date = st.select_slider(
        "Select Historical Date",
        options=date_options,
        value=st.session_state.selected_hist_date,
        key="selected_hist_date"
    )

    hist_row = daily[daily["date"].dt.date == selected_date].iloc[0]
    hist_load = hist_row["actual_load"]
    hist_price = hist_row["actual_price"]
    hist_prob = hist_row["model_spike_probability"]
    hist_dec = hist_row["model_decision"]
    actual_spike = hist_row["actual_spike"]
    load_diff = hist_load - predicted_load

    st.metric("Actual Load", f"{int(hist_load):,}")
    st.metric("Actual Price", f"${hist_price:,.2f}")
    st.metric("Model Spike Probability", f"{hist_prob:.3f}")
    st.metric("Load Difference", f"{int(load_diff):,}")

    if hist_dec == "HEDGE":
        st.error(f"Model Decision: {hist_dec}")
    elif hist_dec == "WATCH / PARTIAL HEDGE":
        st.warning(f"Model Decision: {hist_dec}")
    else:
        st.success(f"Model Decision: {hist_dec}")

    if actual_spike:
        st.error("Actual Outcome: SPIKE")
    else:
        st.success("Actual Outcome: NO SPIKE")

# --- DASHBOARD CHARTS ---
st.subheader("Risk and Strategy Dashboard")

# This creates a narrative flow:

# Chart 1 — “What’s the risk?”
# spike probability vs load

# Chart 2 — “Did this strategy work?”
# cumulative savings

# Chart 3 — “Why do we hedge?”
# expected loss vs hedge cost

# That third one is the missing operator lens.

# chart1, chart2, chart3 = st.columns(3)
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("#### Spike Risk Curve")

    fig, ax = plt.subplots(figsize=(7, 3.8))

    ax.plot(load_levels, spike_probs, linewidth=2, label="Risk Curve")
    ax.scatter(predicted_load, prob, s=70, label="Forward Scenario")
    ax.scatter(hist_load, hist_prob, s=70, label="Historical Replay")

    ax.axhline(WATCH_THRESHOLD, linestyle="--", linewidth=1, label="WATCH")
    ax.axhline(HEDGE_THRESHOLD, linestyle="--", linewidth=1, label="HEDGE")
    ax.axvline(watch_load, linestyle=":", linewidth=1)
    ax.axvline(hedge_load, linestyle=":", linewidth=1)

    ax.set_xlabel("ERCOT Load")
    ax.set_ylabel("Spike Probability")
    ax.set_title("Spike Probability vs Load")

    ax.set_xlim(load_levels.min() - 2000, load_levels.max() + 2000)
    ax.set_ylim(0, max(spike_probs) * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", ncol=2, frameon=False)
    fig.tight_layout()

    st.pyplot(fig, use_container_width=True)

with chart2:
    st.markdown("#### Cumulative Savings vs No Hedge")

    pnl = daily.copy()
    pnl = pnl.sort_values("date")
    pnl["cum_savings"] = pnl["savings_vs_no_hedge"].cumsum()

    fig_sav, ax_sav = plt.subplots(figsize=(7, 3.8))

    ax_sav.plot(pnl["date"], pnl["cum_savings"], linewidth=2, label="Cumulative Savings")
    ax_sav.set_title("Cumulative Savings")
    ax_sav.set_xlabel("Date")
    ax_sav.set_ylabel("Savings ($)")

    ax_sav.grid(True, alpha=0.3)
    ax_sav.legend(frameon=False)
    fig_sav.tight_layout()

    st.pyplot(fig_sav, use_container_width=True)

# with chart3:
st.markdown("#### Hedge Decision Frontier")

col_center = st.columns([1, 2, 1])[1]  # centers the chart

with col_center:
    fig_dec, ax_dec = plt.subplots(figsize=(7, 3.8))

    expected_losses = spike_probs * (spike_price - normal_price)

    ax_dec.plot(load_levels, expected_losses, linewidth=2, label="Expected Loss")
    ax_dec.axhline(hedge_cost, linestyle="--", linewidth=1, label="Hedge Cost")
    ax_dec.scatter(predicted_load, expected_loss, s=70, label="Forward Scenario")

    ax_dec.set_xlabel("ERCOT Load")
    ax_dec.set_ylabel("Expected Spike Cost ($/MWh)")
    ax_dec.set_title("")

    ax_dec.grid(True, alpha=0.3)
    ax_dec.legend(frameon=False)
    fig_dec.tight_layout()

    st.pyplot(fig_dec, use_container_width=True)

# --- SIGNAL BACKTEST ---
st.subheader("Signal Backtest")

backtest = daily.copy()
backtest["predicted_alert"] = backtest["watch_signal"]

tp = ((backtest["predicted_alert"]) & (backtest["actual_spike"])).sum()
fp = ((backtest["predicted_alert"]) & (~backtest["actual_spike"])).sum()
tn = ((~backtest["predicted_alert"]) & (~backtest["actual_spike"])).sum()
fn = ((~backtest["predicted_alert"]) & (backtest["actual_spike"])).sum()

total_days = len(backtest)
actual_spike_days = int(backtest["actual_spike"].sum())
predicted_alert_days = int(backtest["predicted_alert"].sum())

precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
accuracy = (tp + tn) / total_days if total_days > 0 else 0.0

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric("Total Days", f"{total_days:,}")
    st.metric("Actual Spike Days", f"{actual_spike_days:,}")
    st.metric("Predicted WATCH+ Days", f"{predicted_alert_days:,}")
with metric_col2:
    st.metric("True Positives", f"{tp:,}")
    st.metric("False Positives", f"{fp:,}")
    st.metric("False Negatives", f"{fn:,}")
with metric_col3:
    st.metric("Precision", f"{precision:.2%}")
    st.metric("Recall", f"{recall:.2%}")
    st.metric("Accuracy", f"{accuracy:.2%}")

st.caption(
    "Backtest treats WATCH / PARTIAL HEDGE or HEDGE as an 'alert' and compares that signal "
    f"against whether the day's max price exceeded ${SPIKE_PRICE_THRESHOLD}/MWh."
)

# --- ECONOMIC IMPACT ---
st.markdown("### Economic Impact")

total_no_hedge_cost = daily["no_hedge_cost"].sum()
total_strategy_cost = daily["strategy_cost"].sum()
total_savings = daily["savings_vs_no_hedge"].sum()
avg_daily_savings = daily["savings_vs_no_hedge"].mean()
hedge_days = (daily["economic_decision"] == "HEDGE").sum()

econ_col1, econ_col2, econ_col3 = st.columns(3)
with econ_col1:
    st.metric("Total No-Hedge Cost", f"${total_no_hedge_cost:,.2f}")
    st.metric("Hedge Days", f"{hedge_days:,}")
with econ_col2:
    st.metric("Total Strategy Cost", f"${total_strategy_cost:,.2f}")
with econ_col3:
    st.metric("Total Savings vs No Hedge", f"${total_savings:,.2f}")
    st.metric("Avg Daily Savings", f"${avg_daily_savings:,.2f}")

# --- DETAIL TABLE ---
display_backtest = backtest[[
    "date",
    "month",
    "actual_load",
    "actual_price",
    "model_spike_probability",
    "model_decision",
    "economic_decision",
    "expected_loss",
    "no_hedge_cost",    
    "strategy_cost",
    "savings_vs_no_hedge",
    "actual_spike"
]].copy()

display_backtest = display_backtest.sort_values("date", ascending=False)
display_backtest["date"] = display_backtest["date"].dt.date
display_backtest["actual_load"] = display_backtest["actual_load"].round(0).astype(int)
display_backtest["actual_price"] = display_backtest["actual_price"].round(2)
display_backtest["model_spike_probability"] = display_backtest["model_spike_probability"].round(3)
display_backtest["expected_loss"] = display_backtest["expected_loss"].round(2)
display_backtest["no_hedge_cost"] = display_backtest["no_hedge_cost"].round(2)
display_backtest["strategy_cost"] = display_backtest["strategy_cost"].round(2)
display_backtest["savings_vs_no_hedge"] = display_backtest["savings_vs_no_hedge"].round(2)

display_backtest = display_backtest.rename(columns={
    "date": "Date",
    "month": "Month",
    "actual_load": "Actual Load",
    "actual_price": "Actual Price",
    "model_spike_probability": "Spike Probability",
    "model_decision": "Signal",
    "economic_decision": "Optimal Action",
    "expected_loss": "Expected Spike Cost",
    "no_hedge_cost": "Spot Cost",
    "strategy_cost": "Hedged Cost",
    "savings_vs_no_hedge": "Savings vs No Hedge",
    "actual_spike": "Actual Spike"
})

display_backtest["Actual Spike"] = display_backtest["Actual Spike"].map({
    True: "YES",
    False: "NO"
})

st.dataframe(display_backtest, use_container_width=True, hide_index=True)