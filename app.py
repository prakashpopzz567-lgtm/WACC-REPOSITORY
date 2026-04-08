import streamlit as st


st.set_page_config(
    page_title="Free WACC Calculator (Step-by-Step) | Finance Tool",
    page_icon="📊",
    layout="centered",
)

# SEO-friendly header and description
st.title("📊 Free WACC Calculator (Step-by-Step)")
st.markdown(
    "Calculate Weighted Average Cost of Capital (WACC) with clear steps. "
    "Designed for finance students, assignments, and exam prep."
)
st.caption(
    "Keywords: WACC calculator, cost of capital, CAPM, finance tool, student finance calculator"
)


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


st.divider()

with st.form("inputs"):
    st.subheader("Capital structure")
    col_e, col_d = st.columns(2)
    equity = col_e.number_input("Equity (E)", min_value=0.0, value=100.0, step=10.0)
    debt = col_d.number_input("Debt (D)", min_value=0.0, value=50.0, step=10.0)

    st.subheader("Cost of capital inputs")
    mode = st.radio(
        "Cost of equity source",
        ("Manual entry", "CAPM (auto)"),
        horizontal=True,
        help="Use your own cost of equity or let CAPM estimate it.",
    )

    capm_inputs = None
    if mode == "Manual entry":
        re_pct = st.number_input(
            "Cost of Equity (%)",
            min_value=0.0,
            value=10.0,
            step=0.1,
            format="%.2f",
        )
    else:
        capm_cols = st.columns(3)
        rf_pct = capm_cols[0].number_input(
            "Risk-free rate (%)",
            min_value=0.0,
            value=4.0,
            step=0.1,
            format="%.2f",
            help="Common proxy: 10-year government bond yield.",
        )
        beta = capm_cols[1].number_input(
            "Beta",
            min_value=0.0,
            value=1.0,
            step=0.05,
            format="%.2f",
            help="Measures stock sensitivity to market moves.",
        )
        rm_pct = capm_cols[2].number_input(
            "Expected market return (%)",
            min_value=0.0,
            value=8.0,
            step=0.1,
            format="%.2f",
            help="Typical long-run equity market assumption.",
        )

        re_capm_pct = capm_cost_of_equity(rf_pct / 100, beta, rm_pct / 100) * 100
        st.info(
            f"CAPM: Re = Rf + beta × (Rm - Rf) → {re_capm_pct:.2f}%",
            icon="📈",
        )
        re_pct = re_capm_pct
        capm_inputs = {"rf_pct": rf_pct, "beta": beta, "rm_pct": rm_pct}

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

if submitted:
    total_value = equity + debt
    if total_value == 0:
        st.error("Equity + Debt cannot be zero. Add at least one positive value.")
    else:
        re = re_pct / 100
        rd = rd_pct / 100
        tax = tax_pct / 100

        wacc_value, equity_weight, debt_weight = compute_wacc(
            equity, debt, re, rd, tax
        )

        st.subheader("Result")
        st.success(f"WACC = {wacc_value * 100:.2f}%")

        st.subheader("Step-by-step breakdown")
        st.write(
            f"Total value V = E + D = {equity:.2f} + {debt:.2f} = {total_value:.2f}"
        )
        st.write(f"Equity weight = E / V = {equity_weight:.4f}")
        st.write(f"Debt weight = D / V = {debt_weight:.4f}")
        st.write(
            f"Equity contribution = {equity_weight:.4f} × {re:.4f} = {equity_weight * re:.4f}"
        )
        st.write(
            f"Debt contribution = {debt_weight:.4f} × {rd:.4f} × (1 - {tax:.4f}) = {debt_weight * rd * (1 - tax):.4f}"
        )
        st.info(
            "WACC blends the required returns from equity and debt based on their share of total capital."
        )

        if capm_inputs:
            st.divider()
            st.subheader("CAPM scenario: beta sensitivity")
            beta_default = float(capm_inputs["beta"])
            beta_scenario = st.slider(
                "Adjust beta to see its impact",
                min_value=0.0,
                max_value=2.5,
                value=beta_default,
                step=0.05,
            )
            rf_dec = capm_inputs["rf_pct"] / 100
            rm_dec = capm_inputs["rm_pct"] / 100
            scenario_re = capm_cost_of_equity(rf_dec, beta_scenario, rm_dec)
            scenario_wacc, _, _ = compute_wacc(
                equity, debt, scenario_re, rd, tax
            )

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Current beta", f"{beta_default:.2f}")
            col_b.metric("Scenario beta", f"{beta_scenario:.2f}")
            col_c.metric("Scenario WACC", f"{scenario_wacc * 100:.2f}%")

            beta_range = [round(beta_default - 0.5 + 0.1 * i, 2) for i in range(11)]
            beta_range = [b for b in beta_range if b >= 0]
            wacc_series = [
                compute_wacc(
                    equity,
                    debt,
                    capm_cost_of_equity(rf_dec, b, rm_dec),
                    rd,
                    tax,
                )[0]
                * 100
                for b in beta_range
            ]
            chart_data = {"beta": beta_range, "WACC (%)": wacc_series}
            st.line_chart(chart_data, x="beta", y="WACC (%)")

            st.caption(
                "Higher beta raises the cost of equity and therefore WACC; lower beta does the opposite."
            )

st.divider()
st.markdown(
    """
**How to use this tool**  
- Use CAPM mode to estimate the cost of equity from market assumptions.  
- Scenario slider shows how sensitive WACC is to beta changes.  
- Keep units consistent: all rates are percentages before calculation.  
"""
)
