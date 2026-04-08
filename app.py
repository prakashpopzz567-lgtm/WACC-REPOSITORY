import os
import datetime as dt
from typing import Optional, Tuple

import requests
import streamlit as st

# --- Page config ---
st.set_page_config(
    page_title="Free WACC Calculator | CAPM & Scenarios",
    page_icon="📊",
    layout="wide",
)

# --- Defaults & session init ---
DEFAULTS = {"equity": 100.0, "debt": 50.0, "risk_free": 4.0, "beta": 1.0, "market_return": 8.0}
for key, val in DEFAULTS.items():
    st.session_state.setdefault(key, val)
st.session_state.setdefault("ticker", "")

# --- Helpers ---
def get_fmp_api_key() -> Optional[str]:
    """Return Financial Modeling Prep API key from secrets or env."""
    return st.secrets.get("FMP_API_KEY") or os.getenv("FMP_API_KEY")


@st.cache_data(ttl=3600)
def fetch_treasury_10y() -> Optional[Tuple[str, float]]:
    """
    Fetch latest 10Y Treasury yield (approximates risk-free rate).
    Source: U.S. Treasury FiscalData.
    """
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/interest_rates"
    params = {
        "filter": "security_desc:eq:MARKET YIELD ON U.S. TREASURY SECURITIES AT 10-YEAR CONSTANT MATURITY, QUARTERLY",
        "sort": "-record_date",
        "page[number]": 1,
        "page[size]": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return None
        row = data[0]
        as_of = row.get("record_date")
        rate = float(row.get("avg_interest_rate"))
        return as_of, rate
    except Exception:
        return None


@st.cache_data(ttl=3600)
def fetch_beta_from_fmp(ticker: str, api_key: str) -> Optional[Tuple[float, Optional[str]]]:
    """Fetch beta (and company name) from Financial Modeling Prep profile endpoint."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        item = data[0]
        beta_val = float(item.get("beta")) if item.get("beta") is not None else None
        name = item.get("companyName")
        if beta_val is None:
            return None
        return beta_val, name
    except Exception:
        return None


def capm_cost_of_equity(risk_free: float, beta: float, market_return: float) -> float:
    """Return cost of equity using CAPM. Inputs are decimals (0.05 = 5%)."""

    return risk_free + beta * (market_return - risk_free)


def compute_wacc(equity: float, debt: float, re: float, rd: float, tax: float):
    """Return WACC and capital weights. Rates are decimals."""

    total_value = equity + debt
    if total_value == 0:
        return None, None, None

    equity_weight = equity / total_value
    debt_weight = debt / total_value
    equity_contribution = equity_weight * re
    debt_contribution = debt_weight * rd * (1 - tax)
    wacc_value = equity_contribution + debt_contribution
    return wacc_value, equity_weight, debt_weight


# --- Hero section ---
hero = st.container()
with hero:
    left, right = st.columns([0.65, 0.35])
    with left:
        st.title("📊 WACC Studio")
        st.markdown(
            "A student-friendly, finance-grade WACC calculator with CAPM, market fetch, and scenario analysis. "
            "Built for clarity, ready for assignments and quick valuations."
        )
        st.caption(
            "Includes CAPM cost of equity, beta sensitivity, and auto-fill options for Treasury yields and market data."
        )
    with right:
        today = dt.date.today().strftime("%b %d, %Y")
        st.metric("Today", today)
        st.metric("Default market return", f"{DEFAULTS['market_return']:.1f}%")
        st.metric("Default risk-free", f"{DEFAULTS['risk_free']:.1f}% (10Y proxy)")

st.divider()

# --- Data & input panel ---
st.subheader("Input panel")
st.write("Fill in capital structure, pick cost of equity method, or auto-fill with market data.")

input_col1, input_col2 = st.columns([0.65, 0.35])
with input_col2:
    st.markdown("**Auto-fill / Fetch market inputs**")
    ticker = st.text_input(
        "Company ticker (optional, e.g., AAPL)",
        value=st.session_state["ticker"],
        max_chars=10,
    ).upper()
    st.session_state["ticker"] = ticker

    auto_beta = None
    auto_risk_free = None
    fmp_key = get_fmp_api_key()

    fetch_clicked = st.button("Fetch latest data", use_container_width=True)
    if fetch_clicked:
        with st.spinner("Fetching market data..."):
            if fmp_key and ticker:
                beta_result = fetch_beta_from_fmp(ticker, fmp_key)
                if beta_result:
                    auto_beta, company_name = beta_result
                    st.success(f"Beta for {company_name or ticker}: {auto_beta:.2f}")
                    st.session_state["beta"] = round(auto_beta, 2)
                else:
                    st.warning("Could not fetch beta for this ticker.")
            elif ticker and not fmp_key:
                st.info("Add FMP_API_KEY to use auto beta fetch, or enter beta manually.")

            treasury = fetch_treasury_10y()
            if treasury:
                as_of, rf = treasury
                auto_risk_free = rf
                st.success(f"10Y Treasury (as of {as_of}): {rf:.2f}%")
                st.session_state["risk_free"] = round(rf, 2)
            else:
                st.warning("Could not fetch Treasury yield; keeping your current risk-free input.")

    st.markdown(
        """
        *Sources*: U.S. Treasury FiscalData for 10Y yield; Financial Modeling Prep profile for beta (if `FMP_API_KEY` provided).
        """
    )

with input_col1:
    with st.form("calculator"):
        st.markdown("**Capital structure**")
        equity = st.number_input(
            "Equity (E)",
            min_value=0.0,
            value=float(st.session_state["equity"]),
            step=10.0,
        )
        debt = st.number_input(
            "Debt (D)",
            min_value=0.0,
            value=float(st.session_state["debt"]),
            step=10.0,
        )

        st.markdown("**Cost of equity**")
        mode = st.radio(
            "Choose method",
            ("Manual entry", "CAPM (auto)"),
            horizontal=True,
            help="Use your own cost of equity or let CAPM compute it.",
        )

        if mode == "Manual entry":
            re_pct = st.number_input(
                "Cost of Equity (%)",
                min_value=0.0,
                value=st.session_state.get("re_manual", 10.0),
                step=0.1,
                format="%.2f",
            )
            st.session_state["re_manual"] = re_pct
            capm_inputs = None
        else:
            capm_cols = st.columns(3)
            rf_pct = capm_cols[0].number_input(
                "Risk-free rate (%)",
                min_value=0.0,
                value=float(st.session_state["risk_free"]),
                step=0.1,
                format="%.2f",
                help="Using 10Y Treasury as a common WACC proxy.",
            )
            beta = capm_cols[1].number_input(
                "Beta",
                min_value=0.0,
                value=float(st.session_state["beta"]),
                step=0.05,
                format="%.2f",
                help="Stock sensitivity to market moves.",
            )
            rm_pct = capm_cols[2].number_input(
                "Expected market return (%)",
                min_value=0.0,
                value=float(st.session_state["market_return"]),
                step=0.1,
                format="%.2f",
                help="Typical long-run equity market assumption.",
            )
            re_capm_pct = capm_cost_of_equity(rf_pct / 100, beta, rm_pct / 100) * 100
            st.info(f"CAPM: Re = Rf + β × (Rm - Rf) → **{re_capm_pct:.2f}%**", icon="📈")
            re_pct = re_capm_pct
            capm_inputs = {"rf_pct": rf_pct, "beta": beta, "rm_pct": rm_pct}

        st.markdown("**Cost of debt & tax**")
        rd_pct = st.number_input(
            "Cost of Debt (%)",
            min_value=0.0,
            value=5.0,
            step=0.1,
            format="%.2f",
        )
        tax_pct = st.number_input(
            "Tax Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=0.5,
            format="%.2f",
        )

        submitted = st.form_submit_button("Calculate WACC", type="primary")

# --- Results and scenarios ---
if submitted:
    total_value = equity + debt
    if total_value == 0:
        st.error("Equity + Debt cannot be zero. Add at least one positive value.")
    else:
        re = re_pct / 100
        rd = rd_pct / 100
        tax = tax_pct / 100

        wacc_value, equity_weight, debt_weight = compute_wacc(equity, debt, re, rd, tax)

        st.subheader("Summary")
        card1, card2, card3 = st.columns(3)
        card1.metric("WACC", f"{wacc_value * 100:.2f}%")
        card2.metric("Equity weight", f"{equity_weight:.2%}")
        card3.metric("Debt weight", f"{debt_weight:.2%}")

        with st.expander("Step-by-step breakdown", expanded=True):
            st.write(f"Total value V = E + D = {equity:.2f} + {debt:.2f} = {total_value:.2f}")
            st.write(f"Equity weight = E / V = {equity_weight:.4f}")
            st.write(f"Debt weight = D / V = {debt_weight:.4f}")
            st.write(
                f"Equity contribution = {equity_weight:.4f} × {re:.4f} = {equity_weight * re:.4f}"
            )
            st.write(
                f"Debt contribution = {debt_weight:.4f} × {rd:.4f} × (1 - {tax:.4f}) = "
                f"{debt_weight * rd * (1 - tax):.4f}"
            )
            st.info("WACC blends required returns from equity and debt based on their share of total capital.")

        # Scenario analysis
        st.subheader("Scenario analysis")
        scen_col1, scen_col2 = st.columns([0.55, 0.45])
        with scen_col1:
            beta_scenario = st.slider(
                "Adjust beta to see its impact",
                min_value=0.0,
                max_value=2.5,
                value=capm_inputs["beta"] if capm_inputs else DEFAULTS["beta"],
                step=0.05,
            )
            leverage_shift = st.slider(
                "Change capital mix (equity ↑ / debt ↓)",
                min_value=-50,
                max_value=50,
                value=0,
                step=5,
                help="Positive values tilt towards more equity; negative towards more debt (in % of current amounts).",
            )

        with scen_col2:
            adj_equity = equity * (1 + leverage_shift / 100)
            adj_debt = max(debt * (1 - leverage_shift / 100), 0)
            scenario_re = capm_cost_of_equity(
                (capm_inputs["rf_pct"] if capm_inputs else DEFAULTS["risk_free"]) / 100,
                beta_scenario,
                (capm_inputs["rm_pct"] if capm_inputs else DEFAULTS["market_return"]) / 100,
            )
            scenario_wacc, _, _ = compute_wacc(adj_equity, adj_debt, scenario_re, rd, tax)
            if scenario_wacc is not None:
                st.metric("Scenario WACC", f"{scenario_wacc * 100:.2f}%")
            else:
                st.warning("Scenario could not be computed (capital structure became zero).")
            st.caption(
                "Scenario recalculates WACC using adjusted beta and capital mix while holding cost of debt and tax constant."
            )

        # Chart: WACC vs beta
        beta_range = [round(0.5 + 0.1 * i, 2) for i in range(21)]
        rf_base = (capm_inputs["rf_pct"] if capm_inputs else DEFAULTS["risk_free"]) / 100
        rm_base = (capm_inputs["rm_pct"] if capm_inputs else DEFAULTS["market_return"]) / 100
        wacc_series = [
            compute_wacc(
                equity,
                debt,
                capm_cost_of_equity(rf_base, b, rm_base),
                rd,
                tax,
            )[0]
            * 100
            for b in beta_range
        ]
        st.line_chart({"beta": beta_range, "WACC (%)": wacc_series}, x="beta", y="WACC (%)")

st.divider()
with st.expander("Assumptions & data sources", expanded=False):
    st.markdown(
        """
- **Risk-free rate**: 10Y U.S. Treasury (FiscalData API). If fetch fails, defaults to your manual input.
- **Beta**: Financial Modeling Prep profile endpoint (requires `FMP_API_KEY` in Streamlit secrets). Fallback: manual entry.
- **Market return**: Default 8.0% (editable).  
- **CAPM**: Re = Rf + β × (Rm − Rf).  
- **WACC**: weights based on E and D, debt after-tax.  
- **Caching**: fetched data cached for 1 hour to reduce API calls.
"""
    )

# --- Styling tweaks ---
st.markdown(
    """
<style>
section.main > div {padding-top: 10px;}
.stButton button {width: 100%;}
.stMetric {background: #f8fafc; border-radius: 12px; padding: 10px;}
</style>
""",
    unsafe_allow_html=True,
)
