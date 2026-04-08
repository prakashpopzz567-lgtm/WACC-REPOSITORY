import streamlit as st

st.set_page_config(
    page_title="Free WACC Calculator (Step-by-Step) | Finance Tool",
    layout="centered"
)

st.title("📊 WACC Calculator")
st.write("Calculate Weighted Average Cost of Capital with a step-by-step breakdown.")

E = st.number_input("Equity (E)", min_value=0.0, value=100.0)
D = st.number_input("Debt (D)", min_value=0.0, value=50.0)
Re = st.number_input("Cost of Equity (%)", min_value=0.0, value=10.0) / 100
Rd = st.number_input("Cost of Debt (%)", min_value=0.0, value=5.0) / 100
T = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=30.0) / 100

if st.button("Calculate WACC"):
    V = E + D

    if V == 0:
        st.error("Equity + Debt cannot be zero.")
    else:
        equity_weight = E / V
        debt_weight = D / V
        equity_contribution = equity_weight * Re
        debt_contribution = debt_weight * Rd * (1 - T)
        wacc = equity_contribution + debt_contribution

        st.header("📈 Result")
        st.success(f"WACC = {wacc * 100:.2f}%")

        st.header("🧮 Step-by-Step Breakdown")
        st.write(f"Total Value (V) = E + D = {E} + {D} = {V}")
        st.write(f"Equity Weight = E / V = {E} / {V} = {equity_weight:.2f}")
        st.write(f"Debt Weight = D / V = {D} / {V} = {debt_weight:.2f}")
        st.write(
            f"Equity Contribution = {equity_weight:.2f} × {Re:.2f} = {equity_contribution:.4f}"
        )
        st.write(
            f"Debt Contribution = {debt_weight:.2f} × {Rd:.2f} × (1 - {T:.2f}) = {debt_contribution:.4f}"
        )
        st.write(f"Final WACC = {equity_contribution:.4f} + {debt_contribution:.4f}")

        st.header("🧠 Simple Explanation")
        st.info(
            "WACC represents the average cost a company pays for its capital "
            "(both equity and debt), weighted by their proportions."
        )
