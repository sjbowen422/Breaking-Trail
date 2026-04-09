import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import random

# -----------------------------
# Constants and configuration
# -----------------------------

START_DATE = dt.date(2025, 1, 1)
END_DATE = dt.date(2025, 12, 31)

MARKETING_START_DATE = dt.date(2025, 2, 1)
VIRAL_WINDOW_START = dt.date(2025, 5, 1)
VIRAL_WINDOW_END = dt.date(2025, 6, 15)

BASE_DEMAND = 120  # baseline daily demand units
BASE_PRICE = 100.0

MACHINE_COST = 25000
MACHINE_DAILY_CAPACITY = 80
MACHINE_DAILY_FIXED_COST = 400

KIT_COST = 20
VARIABLE_COST_PER_UNIT = 30

MAX_DAYS = (END_DATE - START_DATE).days + 1

# Marketing tiers: (tier, daily_cost, demand_boost_pct)
MARKETING_TIERS = [
    (1, 0, 0.00),
    (2, 500, 0.05),
    (3, 1000, 0.10),
    (4, 3000, 0.25),
    (5, 7000, 0.35),
    (6, 12000, 0.45),
    (7, 20000, 0.55),
]

# -----------------------------
# Utility functions
# -----------------------------

def get_marketing_tier_info(tier: int):
    for t, cost, boost in MARKETING_TIERS:
        if t == tier:
            return cost, boost
    return 0, 0.0


def date_range(start: dt.date, end: dt.date):
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def init_state():
    if "initialized" in st.session_state:
        return

    st.session_state.initialized = True

    st.session_state.current_date = START_DATE
    st.session_state.day_index = 0

    st.session_state.cash = 500000.0
    st.session_state.machines = 3
    st.session_state.backlog = 0
    st.session_state.kits_on_hand = 0

    st.session_state.price = BASE_PRICE
    st.session_state.marketing_tier = 1

    st.session_state.daily_history = []

    st.session_state.autoplay = False
    st.session_state.autoplay_speed = 1

    st.session_state.viral_triggered = False
    st.session_state.viral_threshold = random.randint(150000, 350000)
    st.session_state.cumulative_marketing_spend = 0.0

    st.session_state.marketing_effectiveness_multiplier = 1.0
    st.session_state.oversaturation_triggered = False
    st.session_state.missed_viral_penalty_applied = False

    st.session_state.cash_burn_counter = 0

    st.session_state.trending_warning_shown = False
    st.session_state.missed_viral_checked = False

    st.session_state.events = []

    st.session_state.show_viral_popup = False
    st.session_state.show_crisis_popup = False
    st.session_state.show_autopilot_popup = False
    st.session_state.show_oversaturation_popup = False

    st.session_state.crisis_triggered = False
    st.session_state.crisis_start_date = dt.date(2025, 7, 1)
    st.session_state.crisis_end_date = dt.date(2025, 7, 31)

    st.session_state.celebrity_event_date = dt.date(2025, 4, 10)
    st.session_state.celebrity_triggered = False

    st.session_state.autopilot_active = False

    st.session_state.viral_multiplier = 1.0
    st.session_state.celebrity_multiplier = 1.0
    st.session_state.crisis_multiplier = 1.0

    st.session_state.oversaturation_multiplier = 1.0

    st.session_state.last_revenue = 0.0
    st.session_state.last_marketing_cost = 0.0


def record_event(message: str, level: str = "info"):
    st.session_state.events.insert(0, {"message": message, "level": level, "date": st.session_state.current_date})


def compute_demand_for_day(current_date: dt.date) -> int:
    base = BASE_DEMAND

    price_factor = max(0.1, 1.0 - (st.session_state.price - BASE_PRICE) / 200.0)

    marketing_cost, marketing_boost = get_marketing_tier_info(st.session_state.marketing_tier)

    marketing_effect = 1.0
    if current_date >= MARKETING_START_DATE:
        marketing_effect += marketing_boost

    marketing_effect *= st.session_state.marketing_effectiveness_multiplier
    marketing_effect *= st.session_state.oversaturation_multiplier

    viral_effect = st.session_state.viral_multiplier
    celebrity_effect = st.session_state.celebrity_multiplier
    crisis_effect = st.session_state.crisis_multiplier

    noise = np.random.normal(1.0, 0.05)

    demand = base * price_factor * marketing_effect * viral_effect * celebrity_effect * crisis_effect * noise
    return max(0, int(round(demand)))


def apply_special_events(current_date: dt.date):
    if (not st.session_state.celebrity_triggered) and current_date == st.session_state.celebrity_event_date:
        st.session_state.celebrity_triggered = True
        st.session_state.celebrity_multiplier = 1.4
        record_event("Celebrity endorsement! Demand surges.", "success")

    if st.session_state.celebrity_triggered and current_date > st.session_state.celebrity_event_date + dt.timedelta(days=14):
        st.session_state.celebrity_multiplier = 1.0

    if (not st.session_state.crisis_triggered) and current_date == st.session_state.crisis_start_date:
        st.session_state.crisis_triggered = True
        st.session_state.crisis_multiplier = 0.5
        record_event("Supply chain crisis hits! Demand and capacity are disrupted.", "error")
        st.session_state.show_crisis_popup = True

    if st.session_state.crisis_triggered and current_date > st.session_state.crisis_end_date:
        st.session_state.crisis_multiplier = 1.0


def check_viral_and_marketing_effects(current_date: dt.date, marketing_cost_today: float, revenue_today: float):
    if current_date >= MARKETING_START_DATE:
        st.session_state.cumulative_marketing_spend += marketing_cost_today

    st.session_state.last_marketing_cost = marketing_cost_today
    st.session_state.last_revenue = revenue_today

    if marketing_cost_today > revenue_today:
        st.session_state.cash_burn_counter += 1
    else:
        st.session_state.cash_burn_counter = 0

    if st.session_state.cash_burn_counter >= 5:
        record_event("CFO: We’re burning cash faster than we’re earning it. Recommend scaling back marketing.", "warning")
        st.session_state.cash_burn_counter = 0

    if (not st.session_state.viral_triggered
        and current_date >= VIRAL_WINDOW_START
        and current_date <= VIRAL_WINDOW_END
        and st.session_state.cumulative_marketing_spend >= st.session_state.viral_threshold):
        st.session_state.viral_triggered = True
        st.session_state.viral_multiplier = 1.8
        st.session_state.show_viral_popup = True
        record_event("Owata goes viral! Demand explodes.", "success")

    if (not st.session_state.trending_warning_shown
        and not st.session_state.viral_triggered
        and current_date >= VIRAL_WINDOW_START
        and st.session_state.cumulative_marketing_spend >= 0.9 * st.session_state.viral_threshold):
        st.session_state.trending_warning_shown = True
        record_event("Your marketing team reports Owata is trending. A viral moment may be imminent.", "info")

    if (not st.session_state.missed_viral_penalty_applied
        and current_date > VIRAL_WINDOW_END
        and not st.session_state.viral_triggered):
        st.session_state.missed_viral_penalty_applied = True
        st.session_state.marketing_effectiveness_multiplier *= 0.8
        record_event("Owata failed to catch the wave. Marketing effectiveness drops for the rest of the year.", "warning")

    if (not st.session_state.oversaturation_triggered
        and st.session_state.cumulative_marketing_spend > 2 * st.session_state.viral_threshold):
        st.session_state.oversaturation_triggered = True
        st.session_state.oversaturation_multiplier *= 0.8
        st.session_state.show_oversaturation_popup = True
        record_event("Our marketing is oversaturated. Consumers are tuning us out.", "warning")


def simulate_one_day():
    current_date = st.session_state.current_date

    apply_special_events(current_date)

    marketing_cost, _ = get_marketing_tier_info(st.session_state.marketing_tier)
    if current_date < MARKETING_START_DATE:
        marketing_cost_today = 0.0
    else:
        marketing_cost_today = float(marketing_cost)

    capacity = st.session_state.machines * MACHINE_DAILY_CAPACITY
    if st.session_state.crisis_multiplier < 1.0:
        capacity = int(capacity * 0.7)

    demand_today = compute_demand_for_day(current_date)
    total_demand = demand_today + st.session_state.backlog

    units_produced = min(capacity, total_demand, st.session_state.kits_on_hand)
    st.session_state.kits_on_hand -= units_produced

    units_sold = min(units_produced, total_demand)
    st.session_state.backlog = max(0, total_demand - units_sold)

    revenue_today = units_sold * st.session_state.price

    machine_fixed_costs = st.session_state.machines * MACHINE_DAILY_FIXED_COST
    variable_costs = units_produced * VARIABLE_COST_PER_UNIT

    total_costs = machine_fixed_costs + variable_costs + marketing_cost_today
    profit_today = revenue_today - total_costs

    st.session_state.cash += profit_today

    st.session_state.daily_history.append({
        "date": current_date,
        "demand": demand_today,
        "total_demand": total_demand,
        "units_produced": units_produced,
        "units_sold": units_sold,
        "backlog": st.session_state.backlog,
        "revenue": revenue_today,
        "marketing_cost": marketing_cost_today,
        "machine_fixed_costs": machine_fixed_costs,
        "variable_costs": variable_costs,
        "profit": profit_today,
        "cash": st.session_state.cash,
        "price": st.session_state.price,
        "marketing_tier": st.session_state.marketing_tier,
        "machines": st.session_state.machines,
        "kits_on_hand": st.session_state.kits_on_hand,
    })

    check_viral_and_marketing_effects(current_date, marketing_cost_today, revenue_today)

    st.session_state.day_index += 1
    st.session_state.current_date = current_date + dt.timedelta(days=1)


def reset_game():
    keys = list(st.session_state.keys())
    for k in keys:
        del st.session_state[k]
    init_state()


def render_popups():
    if st.session_state.show_crisis_popup:
        with st.modal("Supply Chain Crisis"):
            st.write("A major supply chain crisis has hit. Capacity and demand are disrupted for several weeks.")
            if st.button("Continue", key="crisis_continue"):
                st.session_state.show_crisis_popup = False

    if st.session_state.show_viral_popup:
        with st.modal("Owata Goes Viral!"):
            st.write("Owata has gone viral! Demand surges as social media explodes with attention.")
            if st.button("Ride the Wave", key="viral_continue"):
                st.session_state.show_viral_popup = False

    if st.session_state.show_autopilot_popup:
        with st.modal("Autopilot Active"):
            st.write("Autopilot is active. Machine decisions are locked.")
            if st.button("Got it", key="autopilot_continue"):
                st.session_state.show_autopilot_popup = False

    if st.session_state.show_oversaturation_popup:
        with st.modal("Oversaturation Warning"):
            st.write("Our marketing is oversaturated. Consumers are tuning us out.")
            st.write("CFO: We recommend reducing marketing spend immediately.")
            if st.button("Understood", key="oversaturation_continue"):
                st.session_state.show_oversaturation_popup = False


def render_controls():
    st.sidebar.header("Decisions")

    st.sidebar.markdown("**Price**")
    st.session_state.price = st.sidebar.slider(
        "Set daily price",
        min_value=60.0,
        max_value=160.0,
        value=st.session_state.price,
        step=5.0,
    )

    st.sidebar.markdown("**Marketing (effects begin February 1)**")
    tier_labels = [f"Tier {t} (${cost}/day, +{int(boost*100)}%)" for t, cost, boost in MARKETING_TIERS]
    tier_values = [t for t, _, _ in MARKETING_TIERS]
    current_index = tier_values.index(st.session_state.marketing_tier)
    selected_index = st.sidebar.selectbox(
        "Marketing intensity",
        options=list(range(len(tier_values))),
        format_func=lambda i: tier_labels[i],
        index=current_index,
    )
    st.session_state.marketing_tier = tier_values[selected_index]

    st.sidebar.markdown("**Capacity**")
    if st.sidebar.button("Buy 1 Machine (-$25,000)"):
        if st.session_state.cash >= MACHINE_COST:
            st.session_state.cash -= MACHINE_COST
            st.session_state.machines += 1
            record_event("Purchased 1 additional machine.", "info")
        else:
            record_event("Not enough cash to buy a machine.", "error")

    st.sidebar.markdown("**Kits**")
    kits_to_buy = st.sidebar.number_input("Kits to buy today", min_value=0, max_value=2000, value=0, step=50)
    if st.sidebar.button("Purchase Kits"):
        total_kit_cost = kits_to_buy * KIT_COST
        if st.session_state.cash >= total_kit_cost:
            st.session_state.cash -= total_kit_cost
            st.session_state.kits_on_hand += kits_to_buy
            record_event(f"Purchased {kits_to_buy} kits.", "info")
        else:
            record_event("Not enough cash to buy kits.", "error")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Autoplay**")
    st.session_state.autoplay = st.sidebar.checkbox("Run automatically", value=st.session_state.autoplay)
    st.session_state.autoplay_speed = st.sidebar.slider(
        "Days per click (when autoplay is on)",
        min_value=1,
        max_value=10,
        value=st.session_state.autoplay_speed,
    )

    if st.sidebar.button("Reset Simulation"):
        reset_game()
        st.experimental_rerun()


def render_header():
    st.title("Owata Operations Simulator")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Date", st.session_state.current_date.isoformat())
    col2.metric("Cash", f"${st.session_state.cash:,.0f}")
    col3.metric("Machines", st.session_state.machines)
    col4.metric("Backlog", st.session_state.backlog)

    st.markdown(
        "> Marketing effects begin **February 1**. Some long‑term effects of marketing are not explicitly disclosed."
    )


def render_events_panel():
    st.subheader("Recent Events")
    if not st.session_state.events:
        st.write("No major events yet.")
        return

    for event in st.session_state.events[:6]:
        if event["level"] == "error":
            st.error(f"{event['date']}: {event['message']}")
        elif event["level"] == "warning":
            st.warning(f"{event['date']}: {event['message']}")
        elif event["level"] == "success":
            st.success(f"{event['date']}: {event['message']}")
        else:
            st.info(f"{event['date']}: {event['message']}")


def render_history():
    if not st.session_state.daily_history:
        return

    df = pd.DataFrame(st.session_state.daily_history)
    df_display = df[["date", "demand", "units_sold", "backlog", "revenue", "profit", "cash", "price", "marketing_tier"]]
    st.subheader("Daily Performance")
    st.dataframe(df_display.tail(30), use_container_width=True)

    st.subheader("Key Trends")
    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(df.set_index("date")[["revenue", "profit"]])
    with col2:
        st.line_chart(df.set_index("date")[["demand", "units_sold", "backlog"]])


def main():
    init_state()

    render_popups()
    render_header()
    render_controls()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        if st.button("Advance 1 Day"):
            if st.session_state.current_date <= END_DATE:
                simulate_one_day()
        if st.session_state.autoplay:
            for _ in range(st.session_state.autoplay_speed):
                if st.session_state.current_date <= END_DATE:
                    simulate_one_day()

        render_history()

    with col_right:
        render_events_panel()

    if st.session_state.current_date > END_DATE:
        st.success("Simulation complete. You’ve reached the end of the year.")


if __name__ == "__main__":
    main()
