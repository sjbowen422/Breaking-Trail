import streamlit as st
import datetime as dt
import random

# =========================
# CONFIG & CONSTANTS
# =========================

st.set_page_config(page_title="Owata Steel Water Bottle Simulator", layout="wide")

START_DATE = dt.date(2025, 1, 1)
END_DATE = dt.date(2025, 12, 31)

CELEB_START = dt.date(2025, 3, 15)
CELEB_END = dt.date(2025, 4, 30)
VIRAL_DATE = dt.date(2025, 5, 1)
CRISIS_DATE = dt.date(2025, 7, 31)
RECOVERY_START = dt.date(2025, 8, 1)
AUTOPILOT_DATE = dt.date(2025, 11, 1)

BASE_DEMAND = 300

MACHINE_COST = 5000
MACHINE_DAILY_OP_COST = 150
MACHINE_SELLBACK = 500

# =========================
# BASE64 SILHOUETTES (placeholder black square)
# =========================

BLACK_SQUARE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAFklEQVR4nO3BMQEAAADCoPVPbQ0PoAAAAAAAAAAA"
)

def img_tag(b64, w=256):
    return f"<img src='data:image/png;base64,{b64}' width='{w}' />"

SILHOUETTE_MUSCLE = BLACK_SQUARE_BASE64
SILHOUETTE_BIG_HAIR = BLACK_SQUARE_BASE64
SILHOUETTE_ROCKET = BLACK_SQUARE_BASE64
SILHOUETTE_COWBOY = BLACK_SQUARE_BASE64
SILHOUETTE_ANGRY = BLACK_SQUARE_BASE64

# =========================
# SESSION STATE
# =========================

def init_state():
    ss = st.session_state
    if "current_date" not in ss:
        ss.current_date = START_DATE
    if "cash" not in ss:
        ss.cash = 50000.0
    if "machines" not in ss:
        ss.machines = {"Cutting": 1, "Forming": 1, "Finishing": 1}
    if "desired_machines" not in ss:
        ss.desired_machines = ss.machines.copy()
    if "kits_on_hand" not in ss:
        ss.kits_on_hand = 500
    if "backlog" not in ss:
        ss.backlog = 0
    if "yesterday_demand" not in ss:
        ss.yesterday_demand = 0
    if "yesterday_sold" not in ss:
        ss.yesterday_sold = 0
    if "yesterday_profit" not in ss:
        ss.yesterday_profit = 0.0
    if "cumulative_profit" not in ss:
        ss.cumulative_profit = 0.0
    if "marketing_tier" not in ss:
        ss.marketing_tier = 1
    if "price" not in ss:
        ss.price = 25.0
    if "autoplay" not in ss:
        ss.autoplay = False
    if "recent_events" not in ss:
        ss.recent_events = []
    if "show_celeb_popup" not in ss:
        ss.show_celeb_popup = False
    if "celeb_triggered" not in ss:
        ss.celeb_triggered = False
    if "show_viral_popup" not in ss:
        ss.show_viral_popup = False
    if "viral_triggered" not in ss:
        ss.viral_triggered = False
    if "show_crisis_popup" not in ss:
        ss.show_crisis_popup = False
    if "crisis_triggered" not in ss:
        ss.crisis_triggered = False
    if "crisis_theme" not in ss:
        ss.crisis_theme = None
    if "autopilot" not in ss:
        ss.autopilot = False
    if "day_counter" not in ss:
        ss.day_counter = 0

init_state()

# =========================
# DEMAND MODEL
# =========================

def marketing_multiplier(date):
    tier = st.session_state.marketing_tier
    base = {1:1.0,2:1.1,3:1.25,4:1.35,5:1.45,6:1.55}[tier]
    if date >= RECOVERY_START:
        base *= 2.0
    return base

def price_multiplier(price):
    if price <= 20: return 1.3
    if price <= 25: return 1.0
    if price <= 30: return 0.8
    return 0.6

def seasonal_multiplier(date):
    if date.month in [6,7,8]: return 1.2
    if date.month in [12,1,2]: return 0.9
    return 1.0

def event_multiplier(date):
    m = 1.0
    if CELEB_START <= date <= CELEB_END:
        m *= 1.3
    if date >= VIRAL_DATE and date < CRISIS_DATE:
        m *= 4.0
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
    d *= random.uniform(0.9,1.1)
    return max(0,int(d))

# =========================
# EVENTS
# =========================

CELEB_QUOTES = [
    ("muscle","I drink three Owata bottles before breakfast.","Definitely Not The Rock"),
    ("big_hair","This bottle changed my life. My therapist is furious.","Oprah-ish"),
    ("rocket","Owata? I thought it was a new crypto coin.","Elon-adjacent"),
    ("cowboy","Best bottle I’ve ever yee’d or haw’d.","Country Singer Vibes"),
]

CRISIS_THEMES = [
    ("political","angry","Owata bottles are now a symbol of the wrong side of the debate.","Anonymous Commentator"),
    ("environmental","angry","Owata bottles are destroying the oceans!","Concerned Influencer"),
    ("celebrity","angry","I can’t believe I bought the bottle that he uses.","Disappointed Fan"),
    ("conspiracy","angry","I heard Owata bottles are made from recycled missile parts.","Guy On The Internet"),
]

def add_event(msg):
    st.session_state.recent_events.insert(0,f"{st.session_state.current_date}: {msg}")
    st.session_state.recent_events = st.session_state.recent_events[:5]

def check_events():
    d = st.session_state.current_date

    if d >= CELEB_START and not st.session_state.celeb_triggered:
        st.session_state.celeb_triggered = True
        st.session_state.show_celeb_popup = True
        add_event("Celebrity endorsement begins (+30% demand).")

    if d >= VIRAL_DATE and not st.session_state.viral_triggered:
        st.session_state.viral_triggered = True
        st.session_state.show_viral_popup = True
        add_event("Owata has gone viral!")

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
        kind,quote,who = random.choice(CELEB_QUOTES)
        img = {
            "muscle":SILHOUETTE_MUSCLE,
            "big_hair":SILHOUETTE_BIG_HAIR,
            "rocket":SILHOUETTE_ROCKET,
            "cowboy":SILHOUETTE_COWBOY
        }[kind]

        st.markdown(f"<div style='text-align:center;'>{img_tag(img,256)}</div>",unsafe_allow_html=True)
        st.write(f"“{quote}” — *{who}*")
        st.write("Demand +30% until April 30.")
        if st.button("Continue"):
            st.session_state.show_celeb_popup = False
            st.experimental_rerun()

def popup_viral():
    if not st.session_state.show_viral_popup:
        return
    with st.modal("Owata Has Gone Viral!"):
        imgs = [SILHOUETTE_MUSCLE,SILHOUETTE_BIG_HAIR,SILHOUETTE_ROCKET,SILHOUETTE_COWBOY]
        random.shuffle(imgs)
        cols = st.columns(3)
        for i in range(3):
            cols[i].markdown(f"<div style='text-align:center;'>{img_tag(imgs[i],128)}</div>",unsafe_allow_html=True)

        st.write("Demand now ~1200/day baseline.")
        if st.button("Continue"):
            st.session_state.show_viral_popup = False
            st.experimental_rerun()

def popup_crisis():
    if not st.session_state.show_crisis_popup:
        return
    with st.modal("Crisis Event"):
        theme,img_key,quote,who = st.session_state.crisis_theme
        st.markdown(f"<div style='text-align:center;'>{img_tag(SILHOUETTE_ANGRY,256)}</div>",unsafe_allow_html=True)
        st.write(f"“{quote}” — *{who}*")
        st.write("Demand has collapsed to 30%. Consider selling machines for $500 each.")
        if st.button("Continue"):
            st.session_state.show_crisis_popup = False
            st.experimental_rerun()

      # =========================
# SIMULATION
# =========================

def daily_capacity():
    return sum(st.session_state.machines.values()) * 150

def simulate_one_day():
    d = st.session_state.current_date
    demand = compute_daily_demand(d)
    cap = daily_capacity()

    # Fulfill backlog
    sold_from_backlog = min(st.session_state.backlog, cap)
    st.session_state.backlog -= sold_from_backlog
    cap -= sold_from_backlog

    # New demand
    sold_today = min(demand, cap)
    lost = demand - sold_today
    st.session_state.backlog += lost

    # Kits
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
    profit = revenue - op_cost - kit_cost

    st.session_state.cash += profit
    st.session_state.cumulative_profit += profit

    st.session_state.yesterday_demand = demand
    st.session_state.yesterday_sold = sold_today
    st.session_state.yesterday_profit = profit

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
    st.title("Owata Steel Water Bottle Simulator")
    st.markdown(
        "<div style='font-size:14px; color:#555;'>Created by <b>Stephen J. Bowen, KFBS EMBA ’27</b></div>",
        unsafe_allow_html=True,
    )

    check_events()

    # Popups pause everything
    if st.session_state.show_celeb_popup:
        popup_celeb()
        return
    if st.session_state.show_viral_popup:
        popup_viral()
        return
    if st.session_state.show_crisis_popup:
        popup_crisis()
        return

    tab_main, tab_analytics = st.tabs(["Dashboard", "Analytics"])

    # =========================
    # MAIN DASHBOARD
    # =========================
    with tab_main:
        left, right = st.columns([2, 1])

        # LEFT SIDE
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

            # Machines
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

            # Pricing & Marketing
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

            # Simulation Controls
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

            # Status
            st.markdown("### Status")
            s1, s2, s3, s4 = st.columns(4)
            s1.write(f"Viral: {'Yes' if st.session_state.viral_triggered else 'No'}")
            s2.write(f"Crisis: {'Yes' if st.session_state.crisis_triggered else 'No'}")
            s3.write(f"Autopilot: {'Yes' if st.session_state.autopilot else 'No'}")
            s4.write(f"Day #: {st.session_state.day_counter}")

            # Recent Events
            st.markdown("### Recent Events")
            if st.session_state.recent_events:
                for e in st.session_state.recent_events:
                    st.write(f"- {e}")
            else:
                st.write("No major events yet.")

        # RIGHT SIDE
