import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nassau Candy Dashboard", page_icon="🍬", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("Nassau Candy Distributor.xlsx")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"])
    df["Lead Time"]  = (df["Ship Date"] - df["Order Date"]).dt.days
    df = df[df["Lead Time"] >= 0]
    df["Delayed"] = df["Lead Time"] > 1400
    df["Speed Tier"] = pd.cut(df["Lead Time"], bins=[0,1000,1400,9999], labels=["Fast","Medium","Slow"])
    factory_map = {
        "Wonka Bar - Nutty Crunch Surprise" : "Lot's O' Nuts",
        "Wonka Bar - Fudge Mallows"         : "Lot's O' Nuts",
        "Wonka Bar -Scrumdiddlyumptious"    : "Lot's O' Nuts",
        "Wonka Bar - Milk Chocolate"        : "Wicked Choccy's",
        "Wonka Bar - Triple Dazzle Caramel" : "Wicked Choccy's",
        "Laffy Taffy"                       : "Sugar Shack",
        "SweeTARTS"                         : "Sugar Shack",
        "Nerds"                             : "Sugar Shack",
        "Fun Dip"                           : "Sugar Shack",
        "Fizzy Lifting Drinks"              : "Sugar Shack",
        "Everlasting Gobstopper"            : "Secret Factory",
        "Hair Toffee"                       : "The Other Factory",
        "Lickable Wallpaper"                : "Secret Factory",
        "Wonka Gum"                         : "Secret Factory",
        "Kazookles"                         : "The Other Factory"
    }
    df["Factory"] = df["Product Name"].map(factory_map)
    df["Route"]   = df["Factory"] + " → " + df["State/Province"]
    return df

df = load_data()

# ── SIDEBAR ──────────────────────────────────────
st.sidebar.title("🎛️ Filters")
all_regions = sorted(df["Region"].dropna().unique())
sel_regions = st.sidebar.multiselect("🌎 Region", all_regions, default=all_regions)
all_modes   = sorted(df["Ship Mode"].dropna().unique())
sel_modes   = st.sidebar.multiselect("🚚 Ship Mode", all_modes, default=all_modes)
min_orders  = st.sidebar.slider("📦 Min Orders per Route", 1, 50, 10)
delay_thresh= st.sidebar.slider("⏱️ Delay Threshold (days)", 900, 1642, 1400, 10)

# ── FILTER DATA ───────────────────────────────────
dff = df[
    df["Region"].isin(sel_regions) &
    df["Ship Mode"].isin(sel_modes)
].copy()
dff["Delayed"] = dff["Lead Time"] > delay_thresh

# ── HEADER ───────────────────────────────────────
st.title("🍬 Nassau Candy Distributor — Shipping Dashboard")
st.markdown("---")

# ── KPI CARDS ────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📦 Total Orders",  f"{len(dff):,}")
k2.metric("⏱️ Avg Lead Time", f"{dff['Lead Time'].mean():.0f} days")
k3.metric("🚨 Delay Rate",    f"{dff['Delayed'].mean()*100:.1f}%")
k4.metric("🛣️ Unique Routes", f"{dff['Route'].nunique():,}")
k5.metric("💰 Total Sales",   f"${dff['Sales'].sum():,.0f}")
st.markdown("---")

# ── TABS ─────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Route Efficiency",
    "🗺️ Geographic Map",
    "🚚 Ship Mode",
    "🔍 Drill-Down"
])

# ══ TAB 1 ════════════════════════════════════════
with tab1:
    st.subheader("Route Performance")
    route_sum = (
        dff.groupby("Route")
        .agg(Avg_Lead=("Lead Time","mean"),
             Total_Orders=("Lead Time","count"),
             Delay_Pct=("Delayed","mean"))
        .reset_index()
    )
    route_sum["Delay_Pct"] *= 100
    route_sum = route_sum[route_sum["Total_Orders"] >= min_orders]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Top 10 Fastest Routes")
        top10 = route_sum.nsmallest(10,"Avg_Lead")
        fig = px.bar(top10, x="Avg_Lead", y="Route", orientation="h",
                     color="Avg_Lead", color_continuous_scale="Greens_r",
                     text=top10["Avg_Lead"].round(0).astype(int).astype(str)+" d")
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"), height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Top 10 Slowest Routes")
        bot10 = route_sum.nlargest(10,"Avg_Lead")
        fig2 = px.bar(bot10, x="Avg_Lead", y="Route", orientation="h",
                      color="Avg_Lead", color_continuous_scale="Reds",
                      text=bot10["Avg_Lead"].round(0).astype(int).astype(str)+" d")
        fig2.update_traces(textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"), height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 🚨 Top 10 Most Delayed Routes")
    delay10 = route_sum.nlargest(10,"Delay_Pct")
    fig3 = px.bar(delay10, x="Delay_Pct", y="Route", orientation="h",
                  color="Delay_Pct", color_continuous_scale="OrRd",
                  text=delay10["Delay_Pct"].round(1).astype(str)+"%")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
                       xaxis_range=[0,100], height=400)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### 📋 Full Route Table")
    show = route_sum.sort_values("Avg_Lead").reset_index(drop=True)
    show.index += 1
    show.columns = ["Route","Avg Lead Time","Total Orders","Delay %"]
    show["Avg Lead Time"] = show["Avg Lead Time"].round(1)
    show["Delay %"]       = show["Delay %"].round(1)
    st.dataframe(show, use_container_width=True, height=300)

# ══ TAB 2 ════════════════════════════════════════
with tab2:
    st.subheader("🗺️ Shipping Performance by State")
    state_sum = (
        dff.groupby("State/Province")
        .agg(Avg_Lead=("Lead Time","mean"),
             Total_Orders=("Lead Time","count"),
             Delay_Pct=("Delayed","mean"))
        .reset_index()
    )
    state_sum["Delay_Pct"] *= 100
    metric_choice = st.radio("Color map by:",
                             ["Avg Lead Time","Delay %","Total Orders"],
                             horizontal=True)
    col_map  = {"Avg Lead Time":"Avg_Lead","Delay %":"Delay_Pct","Total Orders":"Total_Orders"}[metric_choice]
    col_scale= {"Avg Lead Time":"Reds","Delay %":"OrRd","Total Orders":"Blues"}[metric_choice]
    fig_map = px.choropleth(
        state_sum, locations="State/Province", locationmode="USA-states",
        color=col_map, scope="usa", color_continuous_scale=col_scale,
        title=f"{metric_choice} by State"
    )
    fig_map.update_layout(height=500)
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("#### Regional Summary")
    reg = dff.groupby("Region").agg(
        Avg_Lead=("Lead Time","mean"),
        Total_Orders=("Lead Time","count"),
        Delay_Pct=("Delayed","mean")
    ).reset_index()
    reg["Delay_Pct"] *= 100
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(reg, x="Region", y="Avg_Lead", color="Region",
                               title="Avg Lead Time by Region"), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(reg, x="Region", y="Delay_Pct", color="Region",
                               title="Delay Rate by Region"), use_container_width=True)

# ══ TAB 3 ════════════════════════════════════════
with tab3:
    st.subheader("🚚 Ship Mode Comparison")
    mode_sum = dff.groupby("Ship Mode").agg(
        Avg_Lead=("Lead Time","mean"),
        Total_Orders=("Lead Time","count"),
        Delay_Pct=("Delayed","mean"),
        Total_Sales=("Sales","sum")
    ).reset_index()
    mode_sum["Delay_Pct"] *= 100

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(mode_sum, x="Ship Mode", y="Avg_Lead", color="Ship Mode",
                               title="Avg Lead Time by Ship Mode",
                               text=mode_sum["Avg_Lead"].round(0).astype(int).astype(str)+" d"),
                        use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(mode_sum, x="Ship Mode", y="Delay_Pct", color="Ship Mode",
                               title="Delay Rate by Ship Mode",
                               text=mode_sum["Delay_Pct"].round(1).astype(str)+"%"),
                        use_container_width=True)

    st.plotly_chart(px.box(dff, x="Ship Mode", y="Lead Time", color="Ship Mode",
                           title="Lead Time Distribution by Ship Mode"),
                   use_container_width=True)

    tier_mode = dff.groupby(["Ship Mode","Speed Tier"]).size().reset_index(name="Count")
    st.plotly_chart(px.bar(tier_mode, x="Ship Mode", y="Count", color="Speed Tier",
                           barmode="stack",
                           color_discrete_map={"Fast":"green","Medium":"orange","Slow":"red"},
                           title="Fast / Medium / Slow Orders per Ship Mode"),
                   use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(mode_sum, names="Ship Mode", values="Total_Orders",
                               title="Order Volume by Ship Mode"), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(mode_sum, x="Ship Mode", y="Total_Sales", color="Ship Mode",
                               title="Total Sales by Ship Mode"), use_container_width=True)

# ══ TAB 4 ════════════════════════════════════════
with tab4:
    st.subheader("🔍 State-Level Drill-Down")
    all_states = sorted(dff["State/Province"].dropna().unique())
    sel_state  = st.selectbox("Select a State", all_states)
    sdf = dff[dff["State/Province"] == sel_state]

    if sdf.empty:
        st.warning("No data for selected filters.")
    else:
        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Orders",      f"{len(sdf):,}")
        s2.metric("Avg Lead",    f"{sdf['Lead Time'].mean():.0f} days")
        s3.metric("Delay Rate",  f"{sdf['Delayed'].mean()*100:.1f}%")
        s4.metric("Total Sales", f"${sdf['Sales'].sum():,.0f}")

        c1, c2 = st.columns(2)
        with c1:
            rs = sdf.groupby("Route").agg(
                Avg_Lead=("Lead Time","mean"),
                Orders=("Lead Time","count"),
                Delay_Pct=("Delayed","mean")
            ).reset_index()
            rs["Delay_Pct"] *= 100
            st.plotly_chart(px.bar(rs.sort_values("Avg_Lead"),
                                   x="Avg_Lead", y="Route", orientation="h",
                                   color="Delay_Pct", color_continuous_scale="Reds",
                                   title=f"Routes into {sel_state}"),
                           use_container_width=True)
        with c2:
            mc = sdf["Ship Mode"].value_counts().reset_index()
            mc.columns = ["Ship Mode","Count"]
            st.plotly_chart(px.pie(mc, names="Ship Mode", values="Count",
                                   title=f"Ship Mode Mix — {sel_state}"),
                           use_container_width=True)

        st.markdown("#### Order Timeline")
        tdf = sdf[["Order ID","Order Date","Ship Date","Lead Time",
                   "Ship Mode","Factory","Route","Sales"]].sort_values("Order Date").head(100)
        st.dataframe(tdf, use_container_width=True, height=250)

st.markdown("---")
st.caption("Nassau Candy Distributor — Shipping Dashboard | Streamlit + Plotly")