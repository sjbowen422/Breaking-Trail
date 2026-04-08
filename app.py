import streamlit as st
import yfinance as yf
import pandas as pd
import random

st.set_page_config(page_title="Options Bidding Simulator", layout="centered")

# ---------------------------------------------------------
# Initialize session history
# ---------------------------------------------------------
if "history" not in st.session_state:
    st.session_state["history"] = []

MOVES = [-0.20, -0.10, 0.0, 0.10, 0.20]

# ---------------------------------------------------------
# Title
# ---------------------------------------------------------
st.title("📈 Options Bidding Simulator")
st.write("**Created by Stephen J. Bowen**")
st.write("Play multiple rounds, bid on options, and compare your bid to the real market premium.")

# ---------------------------------------------------------
# Step 1 — Choose stock
# ---------------------------------------------------------
ticker = st.text_input("Enter a stock ticker (e.g., AAPL):", "AAPL").upper()

if st.button("Load Expirations"):
    stock = yf.Ticker(ticker)
    valid_exps = stock.options

    if not valid_exps:
        st.error("This stock has no listed options.")
        st.stop()

    st.session_state["valid_exps"] = valid_exps
    st.success("Expirations loaded! Now choose one below.")

if "valid_exps" not in st.session_state:
    st.stop()

valid_exps = st.session_state["valid_exps"]
default_index = 11 if len(valid_exps) > 11 else len(valid_exps) - 1

expiration = st.selectbox(
    "Choose expiration date:",
    valid_exps,
    index=default_index
)

# ---------------------------------------------------------
# Step 2 — Option type behavior
# ---------------------------------------------------------
option_mode = st.radio(
    "Choose option type behavior:",
    ["Random each round", "Always CALL", "Always PUT"]
)

# ---------------------------------------------------------
# Step 3 — Load option chain
# ---------------------------------------------------------
if st.button("Load Option Chain"):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1d")

        if history.empty:
            st.error("No price history available for this ticker.")
            st.stop()

        current_price = history["Close"].iloc[-1]

        chain = stock.option_chain(expiration)
        calls = chain.calls
        puts = chain.puts

        if option_mode == "Random each round":
            option_type = random.choice(["call", "put"])
        elif option_mode == "Always CALL":
            option_type = "call"
        else:
            option_type = "put"

        raw_strikes = (
            calls["strike"].dropna().tolist()
            if option_type == "call"
            else puts["strike"].dropna().tolist()
        )

        lower = current_price * 0.7
        upper = current_price * 1.3
        valid_strikes = [s for s in raw_strikes if lower <= s <= upper]

        if not valid_strikes:
            st.error("No reasonable strikes available.")
            st.stop()

        strike = random.choice(valid_strikes)

        st.session_state["current_price"] = float(current_price)
        st.session_state["calls"] = calls
        st.session_state["puts"] = puts
        st.session_state["strike"] = float(strike)
        st.session_state["option_type"] = option_type
        st.session_state["expiration"] = expiration

        st.success("Option loaded! Scroll down to bid.")

    except Exception as e:
        st.error(f"Error loading data: {e}")

# ---------------------------------------------------------
# Step 4 — Show option details
# ---------------------------------------------------------
if "strike" in st.session_state:

    strike = st.session_state["strike"]
    option_type = st.session_state["option_type"]
    current_price = st.session_state["current_price"]
    expiration = st.session_state["expiration"]

    st.subheader("Your Offered Option")
    st.write(f"**Type:** {option_type.upper()}")
    st.write(f"**Strike Price:** ${strike:.2f}")
    st.write(f"**Expiration:** {expiration}")
    st.write(f"**Current Price:** ${current_price:.2f}")

    student_bid = st.number_input(
        "Enter your premium bid ($):",
        min_value=0.0,
        step=0.25,
        key="premium_input"
    )
    st.session_state["student_bid"] = float(student_bid)

    # ---------------------------------------------------------
    # Step 5 — Reveal results
    # ---------------------------------------------------------
    if st.button("Reveal Market Premium and Outcome"):

        calls = st.session_state["calls"]
        puts = st.session_state["puts"]
        strike = st.session_state["strike"]
        option_type = st.session_state["option_type"]
        current_price = st.session_state["current_price"]
        student_bid = st.session_state["student_bid"]

        row = (
            calls[calls["strike"] == strike]
            if option_type == "call"
            else puts[puts["strike"] == strike]
        )

        if row.empty:
            st.error("Market data unavailable for this strike.")
            st.stop()

        market_premium = float(row["lastPrice"].iloc[0])

        st.subheader("Market Premium")
        st.write(f"Real market premium: **${market_premium:.2f}**")

        # ---------------------------------------------------------
        # Build payoff table
        # ---------------------------------------------------------
        table_rows = []

        for move in MOVES:
            exp_price = current_price * (1 + move)

            if option_type == "call":
                payoff = max(exp_price - strike, 0)
            else:
                payoff = max(strike - exp_price, 0)

            buyer_profit = payoff - student_bid
            writer_profit = -buyer_profit
            moneyness = "ITM" if payoff > 0 else "OTM"

            table_rows.append({
                "Move": f"{int(move * 100)}%",
                "Exp Price": exp_price,
                "Buyer Payoff": payoff,
                "Buyer Profit": buyer_profit,
                "Writer Payoff": -payoff,
                "Writer Profit": writer_profit,
                "ITM/OTM": moneyness
            })

        df = pd.DataFrame(table_rows)

        # ---------------------------------------------------------
        # Dollar formatting
        # ---------------------------------------------------------
        money_cols = ["Exp Price", "Buyer Payoff", "Buyer Profit", "Writer Payoff", "Writer Profit"]

        for col in money_cols:
            df[col] = df[col].map(lambda x: f"${x:,.2f}")

        # ---------------------------------------------------------
        # Universal-compatible styling (no applymap)
        # ---------------------------------------------------------
        def color_text_df(df_in):
            styles = pd.DataFrame("", index=df_in.index, columns=df_in.columns)

            for r in df_in.index:
                for c in df_in.columns:
                    val = df_in.loc[r, c]

                    # Profit coloring
                    if isinstance(val, str) and (val.startswith("$") or val.startswith("-$")):
                        try:
                            num = float(val.replace("$", "").replace(",", ""))
                            if num > 0:
                                styles.loc[r, c] = "color: green"
                            elif num < 0:
                                styles.loc[r, c] = "color: red"
                        except:
                            pass

                    # ITM/OTM coloring
                    if val == "ITM":
                        styles.loc[r, c] = "color: green"
                    if val == "OTM":
                        styles.loc[r, c] = "color: red"

            return styles

        styled_df = df.style.apply(color_text_df, axis=None)

        st.subheader("📊 Payoff Table (Buyer & Writer)")
        st.dataframe(styled_df, use_container_width=True)

        # ---------------------------------------------------------
        # Add to session history
        # ---------------------------------------------------------
        st.session_state["history"].append({
            "symbol": ticker,
            "type": option_type.upper(),
            "strike": strike,
            "expiration": expiration,
            "premium_bid": student_bid,
            "payoff_table": table_rows
        })

        # ---------------------------------------------------------
        # Play Again
        # ---------------------------------------------------------
        if st.button("Play Again"):
            keys_to_clear = [
                "strike", "option_type", "calls", "puts",
                "current_price", "student_bid", "premium_input"
            ]
            for k in keys_to_clear:
                st.session_state.pop(k, None)

            st.session_state["premium_input"] = 0.0
            st.experimental_rerun()