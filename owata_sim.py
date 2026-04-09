import streamlit as st
import datetime as dt
import random

# =========================
# CONSTANTS
# =========================

START_DATE = dt.date(2025, 1, 1)
END_DATE = dt.date(2025, 12, 31)

BASE_DEMAND = 300

MACHINE_COST = 2000
MACHINE_SELLBACK = 500
MACHINE_DAILY_OP_COST = 150

# Event dates
CELEB_START = dt.date(2025, 3, 15)
CELEB_END = dt.date(2025, 4, 30)
CRISIS_DATE = dt.date(2025, 9, 1)
AUTOPILOT_DATE = dt.date(2025, 10, 15)
RECOVERY_START = dt.date(2025, 11, 1)

# New viral system dates
MARKETING_START_DATE = dt.date(2025, 2, 1)
VIRAL_WINDOW_START = dt.date(2025, 5, 1)
VIRAL_WINDOW_END = dt.date(2025, 6, 15)

# Marketing daily cost per tier (1–6)
MARKETING_DAILY_COST = {
    1: 0,
    2: 500,
    3: 1000,
    4: 3000,
    5: 7000,
    6: 12000,
}

# Generic silhouette placeholder (option C)
SILHOUETTE_GENERIC = ""

# =========================
# IMAGE HELPER
# =========================

def img_tag(b64, size):
    if not b64:
        return ""
    return f"<img src='data:image/png;base64,{b64}' width='{size}' />"

# =========================
# SESSION STATE INIT
# =========================

def init_state():
    if "initialized" in st.session_state:
        return

    st.session_state.initialized = True

    st.session_state.current_date = START_DATE
    st.session_state.day_counter = 0

    st.session_state.cash = 50000.0
    st.session_state.cumulative_profit = 0.0

    st.session_state.kits_on_hand = 500
    st.session_state.backlog = 0

    st.session_state.machines = {
        "Paint Bottle": 3,
        "Paint Lid": 3,
        "Assemble": 3,
    }
    st.session_state.desired_machines = {
        "Paint Bottle": 3,
        "Paint Lid": 3,
        "Assemble": 3,
    }

    st.session_state.yesterday_demand = 0
    st.session_state.yesterday_sold = 0
    st.session_state.yesterday_profit = 0.0

    st.session_state.recent_events = []

    st.session_state.celeb_triggered = False
    st.session_state.viral_triggered = False
    st.session_state.crisis_triggered = False
    st.session_state.autopilot = False

    st.session_state.show_celeb_popup = False
    st.session_state.show_viral_popup = False
    st.session_state.show_crisis_popup = False
    st.session_state.show_oversaturation_popup = False

    st.session_state.crisis_theme = None

    st.session_state.price = 25.0
    st.session_state.marketing_tier = 1

    st.session_state.autoplay = False

    # New viral/oversaturation/cash-burn state
    st.session_state.cumulative_marketing_spend = 0.0
    st.session_state.viral_threshold = random.randint(150000, 350000)
    st.session_state.marketing_effectiveness_multiplier = 1.0
    st.session_state.oversaturation_triggered = False
    st.session_state.missed_viral_penalty_applied = False
    st.session_state.trending_warning_shown = False
    st.session_state.cash_burn_counter = 0

# =========================
# DEMAND MODEL
# =========================

def marketing_multiplier(date):
    tier = st.session_state.marketing_tier
    base = {
        1: 1.0,
        2: 1.1,
        3: 1.25,
        4: 1.35,
        5: 1.45,
        6: 1.55,
    }[tier]

    if date >= MARKETING_START_DATE:
        base *= st.session_state.marketing_effectiveness_multiplier

    if st.session_state.viral_triggered:
        base *= 4.0

    if st.session_state.oversaturation_triggered:
        base *= 0.8

    if st.session_state.missed_viral_penalty_applied:
        base *= 0.8

    if date >= RECOVERY_START:
        base *= 2.0

    return base

def price_multiplier(price):
    if price <= 20:
        return 1.3
    if price <= 25:
        return 1.0
    if price <= 30:
        return 0.8
    return 0.6

def seasonal_multiplier(date):
    if date.month in [6, 7, 8]:
        return 1.2
    if date.month in [12, 1, 2]:
        return 0.9
    return 1.0

def event_multiplier(date):
    m = 1.0
    if CELEB_START <= date <= CELEB_END:
        m *= 1.3
    if date >= CRISIS_DATE:
        m *= 0.3
    return m

def compute_daily_demand(date):
    base = BASE_DEMAND
    mkt = marketing_multiplier(date)
    pm = price_multiplier(st.session_state.price)
    seas = seasonal_multiplier(date)
    evt = event_multiplier(date)
    d = base * mkt * pm * seas * evt
    d *= random.uniform(0.9, 1.1)
    return max(0, int(d))

# =========================
# EVENTS
# =========================

CELEB_QUOTES = [
    ("generic", "I drink three Owata bottles before breakfast.", "Definitely Not The Rock"),
    ("generic", "This bottle changed my life. My therapist is furious.", "Oprah-ish"),
    ("generic", "Owata? I thought it was a new crypto coin.", "Elon-adjacent"),
    ("generic", "Best bottle I’ve ever yee’d or haw’d.", "Country Singer Vibes"),
]

CRISIS_THEMES = [
    ("political", "angry", "Owata bottles are now a symbol of the wrong side of the debate.", "Anonymous Commentator"),
    ("environmental", "angry", "Owata bottles are destroying the oceans!", "Concerned Influencer"),
    ("celebrity", "angry", "I can’t believe I bought the bottle that he uses.", "Disappointed Fan"),
    ("conspiracy", "angry", "I heard Owata bottles are made from recycled missile parts.", "Guy On The Internet"),
]

def add_event(msg):
    st.session_state.recent_events.insert(0, f"{st.session_state.current_date}: {msg}")
    st.session_state.recent_events = st.session_state.recent_events[:5]

def check_events():
    d = st.session_state.current_date

    if d >= CELEB_START and not st.session_state.celeb_triggered:
        st.session_state.celeb_triggered = True
        st.session_state.show_celeb_popup = True
        add_event("Celebrity endorsement begins (+30% demand).")

    if d >= CRISIS_DATE and not st.session_state.crisis_triggered:
        st.session_state.crisis_triggered = True
        st.session_state.show_crisis_popup = True
        st.session_state.crisis_theme = random.choice(CRISIS_THEMES)
        add_event("Crisis hits: demand collapses to 30%.")

    if d >= AUTOPILOT_DATE and not st.session_state.autopilot:
        st.session_state.autopilot = True
        add_event("Autopilot engaged: decisions locked.")

# =========================
# POPUPS
# =========================

def popup_celeb():
    if not st.session_state.show_celeb_popup:
        return
    with st.modal("Celebrity Endorsement"):
        kind, quote, who = random.choice(CELEB_QUOTES)
        img = SILHOUETTE_GENERIC
        st.markdown(f"<div style='text-align:center;'>{img_tag(img,256)}</div>", unsafe_allow_html=True)
        st.write(f"“{quote}” — *{who}*")
        st.write("Demand +30% until April 30.")
        if st.button("Continue"):
            st.session_state.show_celeb_popup = False
            st.experimental_rerun()

def popup_viral():
    if not st.session_state.show_viral_popup:
        return
    with st.modal("Owata Has Gone Viral!"):
        cols = st.columns(3)
        for i in range(3):
            cols[i].markdown(
                f"<div style='text-align:center;'>{img_tag(SILHOUETTE_GENERIC,128)}</div>",
                unsafe_allow_html=True,
            )
        st.write("Demand now ~1200/day baseline.")
        if st.button("Continue"):
            st.session_state.show_viral_popup = False
            st.experimental_rerun()

def popup_crisis():
    if not st.session_state.show_crisis_popup:
        return
    with st.modal("Crisis Event"):
        theme, img_key, quote, who = st.session_state.crisis_theme
        st.markdown(
            f"<div style='text-align:center;'>{img_tag(SILHOUETTE_GENERIC,256)}</div>",
            unsafe_allow_html=True,
        )
        st.write(f"“{quote}” — *{who}*")
        st.write("Demand has collapsed to 30%. Consider selling machines for $500 each.")
        if st.button("Continue"):
            st.session_state.show_crisis_popup = False
            st.experimental_rerun()

def popup_oversaturation():
    if not st.session_state.show_oversaturation_popup:
        return
    with st.modal("Oversaturation Warning"):
        cols = st.columns(3)
        sizes = [220, 180, 200]
        for i in range(3):
            cols[i].markdown(
                f"<div style='text-align:center;'>{img_tag(SILHOUETTE_GENERIC,sizes[i])}</div>",
                unsafe_allow_html=True,
            )
        st.write("Our marketing is oversaturated. Consumers are tuning us out.")
        st.write("CFO: We recommend reducing marketing spend immediately.")
        if st.button("Continue", key="oversat_continue"):
            st.session_state.show_oversaturation_popup = False
            st.experimental_rerun()

# =========================
# SIMULATION
# =========================

def daily_capacity():
    return sum(st.session_state.machines.values()) * 150

def update_marketing_and_viral(d, revenue, marketing_cost_today):
    if d >= MARKETING_START_DATE:
        st.session_state.cumulative_marketing_spend += marketing_cost_today

    if marketing_cost_today > revenue:
        st.session_state.cash_burn_counter += 1
    else:
        st.session_state.cash_burn_counter = 0

    if st.session_state.cash_burn_counter >= 5:
        add_event("CFO: We’re burning cash faster than we’re earning it. Recommend scaling back marketing.")
        st.session_state.cash_burn_counter = 0

    if (not st.session_state.viral_triggered
        and d >= VIRAL_WINDOW_START
        and d <= VIRAL_WINDOW_END
        and st.session_state.cumulative_marketing_spend >= st.session_state.viral_threshold):
        st.session_state.viral_triggered = True
        st.session_state.show_viral_popup = True
        add_event("Owata has gone viral!")

    if (not st.session_state.trending_warning_shown
        and not st.session_state.viral_triggered
        and d >= VIRAL_WINDOW_START
        and st.session_state.cumulative_marketing_spend >= 0.9 * st.session_state.viral_threshold):
        st.session_state.trending_warning_shown = True
        add_event("Your marketing team reports Owata is trending. A viral moment may be imminent.")

    if (not st.session_state.missed_viral_penalty_applied
        and d > VIRAL_WINDOW_END
        and not st.session_state.viral_triggered):
        st.session_state.missed_viral_penalty_applied = True
        st.session_state.marketing_effectiveness_multiplier *= 0.8
        add_event("Owata failed to catch the wave. Marketing effectiveness drops for the rest of the year.")

    if (not st.session_state.oversaturation_triggered
        and st.session_state.cumulative_marketing_spend > 2 * st.session_state.viral_threshold):
        st.session_state.oversaturation_triggered = True
        st.session_state.show_oversaturation_popup = True
        add_event("Our marketing is oversaturated. Consumers are tuning us out.")

def simulate_one_day():
    d = st.session_state.current_date
    demand = compute_daily_demand(d)
    cap = daily_capacity()

    sold_from_backlog = min(st.session_state.backlog, cap)
    st.session_state.backlog -= sold_from_backlog
    cap -= sold_from_backlog

    sold_today = min(demand, cap)
    lost = demand - sold_today
    st.session_state.backlog += lost

    kits_needed = sold_today
    if kits_needed > st.session_state.kits_on_hand:
        sold_today = st.session_state.kits_on_hand
        st.session_state.backlog += (kits_needed - sold_today)
        st.session_state.kits_on_hand = 0
        add_event("Stockout of kits.")
    else:
        st.session_state.kits_on_hand -= kits_needed

    revenue = sold_today * st.session_state.price

    op_cost = sum(st.session_state.machines.values()) * MACHINE_DAILY_OP_COST
    kit_cost = sold_today * 5.0

    marketing_cost_today = 0.0
    if d >= MARKETING_START_DATE:
        marketing_cost_today = MARKETING_DAILY_COST.get(st.session_state.marketing_tier, 0)

    profit = revenue - op_cost - kit_cost - marketing_cost_today

    st.session_state.cash += profit
    st.session_state.cumulative_profit += profit

    st.session_state.yesterday_demand = demand
    st.session_state.yesterday_sold = sold_today
    st.session_state.yesterday_profit = profit

    update_marketing_and_viral(d, revenue, marketing_cost_today)

    st.session_state.day_counter += 1
    st.session_state.current_date = d + dt.timedelta(days=1)

    check_events()

# =========================
# MACHINE BUY/SELL
# =========================

def sell_machine(station):
    cur = st.session_state.machines[station]
    if cur > 0:
        st.session_state.machines[station] -= 1
        st.session_state.cash += MACHINE_SELLBACK
        add_event(f"Sold 1 {station} machine for ${MACHINE_SELLBACK}.")
    else:
        add_event(f"No {station} machines left to sell.")

def apply_machine_changes():
    if st.session_state.autopilot:
        return
    cur = st.session_state.machines
    des = st.session_state.desired_machines

    for station in cur.keys():
        c = cur[station]
        d = des[station]
        if d > c:
            delta = d - c
            cost = delta * MACHINE_COST
            if st.session_state.cash >= cost:
                st.session_state.cash -= cost
                cur[station] = d
                add_event(f"Bought {delta} {station} machine(s).")
            else:
                add_event(f"Not enough cash to buy {delta} {station} machine(s).")
                des[station] = c
        elif d < c:
            delta = c - d
            proceeds = delta * MACHINE_SELLBACK
            st.session_state.cash += proceeds
            cur[station] = d
            add_event(f"Sold {delta} {station} machine(s) for ${proceeds}.")

# =========================
# UI
# =========================

def main():
    init_state()

    st.title("Owata Steel Water Bottle Simulator")
    st.markdown(
        "<div style='font-size:14px; color:#555;'>Created by <b>Stephen J. Bowen, KFBS EMBA ’27</b></div>",
        unsafe_allow_html=True,
    )

    check_events()

    if st.session_state.show_celeb_popup:
        popup_celeb()
        return
    if st.session_state.show_viral_popup:
        popup_viral()
        return
    if st.session_state.show_crisis_popup:
        popup_crisis()
        return
    if st.session_state.show_oversaturation_popup:
        popup_oversaturation()
        return

    tab_main, tab_analytics = st.tabs(["Dashboard", "Analytics"])

    with tab_main:
        left, right = st.columns([2, 1])

        with left:
            st.subheader(f"Date: {st.session_state.current_date}")

            st.markdown("### Key Metrics (Yesterday)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Demand", st.session_state.yesterday_demand)
            c2.metric("Units Sold", st.session_state.yesterday_sold)
            c3.metric("Profit", f"${st.session_state.yesterday_profit:,.0f}")

            c4, c5, c6 = st.columns(3)
            c4.metric("Kits on Hand", st.session_state.kits_on_hand)
            c5.metric("Backlog", st.session_state.backlog)
            c6.metric("Cumulative Profit", f"${st.session_state.cumulative_profit:,.0f}")

            st.markdown("### Machines")
            cols = st.columns(3)
            for col, station in zip(cols, st.session_state.machines.keys()):
                with col:
                    st.write(f"**{station}**")
                    st.write(f"Active: {st.session_state.machines[station]}")

                    if st.button(f"Sell 1 {station}", key=f"sell_{station}"):
                        sell_machine(station)
                        st.experimental_rerun()

                    if not st.session_state.autopilot:
                        st.session_state.desired_machines[station] = st.number_input(
                            f"Desired {station}",
                            min_value=0,
                            max_value=20,
                            value=st.session_state.desired_machines[station],
                            key=f"desired_{station}",
                        )

            if not st.session_state.autopilot:
                if st.button("Apply Machine Changes"):
                    apply_machine_changes()
                    st.experimental_rerun()
            else:
                st.info("Autopilot is active. Machine decisions are locked.")

            st.markdown("### Pricing & Marketing")
            if not st.session_state.autopilot:
                st.session_state.price = st.slider(
                    "Price per bottle ($)", 10.0, 40.0, st.session_state.price, 0.5
                )
                st.session_state.marketing_tier = st.slider(
                    "Marketing Tier (1–6)", 1, 6, st.session_state.marketing_tier
                )
            else:
                st.write(f"Price: ${st.session_state.price:.2f}")
                st.write(f"Marketing Tier: {st.session_state.marketing_tier}")

            st.markdown("### Simulation Controls")
            cauto, cstep = st.columns(2)
            with cauto:
                st.session_state.autoplay = st.checkbox(
                    "Autoplay (1 day/step)", value=st.session_state.autoplay
                )
            with cstep:
                if st.button("Advance 1 Day"):
                    simulate_one_day()
                    st.experimental_rerun()

            st.markdown("### Status")
            s1, s2, s3, s4 = st.columns(4)
            s1.write(f"Viral: {'Yes' if st.session_state.viral_triggered else 'No'}")
            s2.write(f"Crisis: {'Yes' if st.session_state.crisis_triggered else 'No'}")
            s3.write(f"Autopilot: {'Yes' if st.session_state.autopilot else 'No'}")
            s4.write(f"Day #: {st.session_state.day_counter}")

            st.markdown("### Recent Events")
            if st.session_state.recent_events:
                for e in st.session_state.recent_events:
                    st.write(f"- {e}")
            else:
                st.write("No major events yet.")

        with right:
            st.markdown("### Quick Info")
            st.write("**Daily Capacity**")
            st.write(f"{daily_capacity()} units/day")
            st.write("**Cash**")
            st.write(f"${st.session_state.cash:,.0f}")
            st.write("**Marketing Multiplier**")
            st.write(f"{marketing_multiplier(st.session_state.current_date):.2f}")
            st.write("**Price Multiplier**")
            st.write(f"{price_multiplier(st.session_state.price):.2f}")
            st.write("**Seasonal Multiplier**")
            st.write(f"{seasonal_multiplier(st.session_state.current_date):.2f}")
            st.write("**Event Multiplier**")
            st.write(f"{event_multiplier(st.session_state.current_date):.2f}")

    with tab_analytics:
        st.subheader("Analytics")
        st.write("Charts coming soon.")

    if st.session_state.autoplay and not (
        st.session_state.show_celeb_popup
        or st.session_state.show_viral_popup
        or st.session_state.show_crisis_popup
        or st.session_state.show_oversaturation_popup
    ):
        if st.session_state.current_date <= END_DATE:
            simulate_one_day()
            st.experimental_rerun()
        else:
            st.session_state.autoplay = False

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()
