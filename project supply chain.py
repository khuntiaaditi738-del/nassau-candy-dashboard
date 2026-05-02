
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_excel("Nassau Candy Distributor.xlsx")
df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"] = pd.to_datetime(df["Ship Date"])
df["Lead Time"] = (df["Ship Date"] - df["Order Date"]).dt.days
df = df[df["Lead Time"] >= 0]
print("=== LEAD TIME STATS ===")
print(df["Lead Time"].describe())
# STEP 4: LABEL SPEED TIER
# Fast = 904-1000 days | Medium = 1001-1400 | Slow = 1401+
# ============================================================
df["Speed Tier"] = pd.cut(
    df["Lead Time"],
    bins=[0, 1000, 1400, 9999],
    labels=["Fast", "Medium", "Slow"]
)

print("\n=== SPEED TIER COUNTS ===")
print(df["Speed Tier"].value_counts())

# ============================================================
# STEP 5: MAP PRODUCTS TO FACTORIES
# ============================================================
factory_map = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

df["Factory"] = df["Product Name"].map(factory_map)
df["Route"] = df["Factory"] + " -> " + df["State/Province"]

print("\n=== SAMPLE ROUTES ===")
print(df[["Factory", "State/Province", "Route"]].head())

# ============================================================
# STEP 6: ROUTE SUMMARY
# ============================================================
route_summary = df.groupby("Route").agg(
    {"Lead Time": ["mean", "count", "std"]}
).reset_index()
route_summary.columns = ["Route", "Average Lead Time", "Total Orders", "Variability"]

# *** KEY FIX: Only keep routes with 10 or more orders ***
# Routes with 1-2 orders will always show 0% or 100% - not useful
route_summary = route_summary[route_summary["Total Orders"] >= 10]

print(f"\n=== ROUTES WITH 10+ ORDERS: {len(route_summary)} routes ===")
print(route_summary.head())

# ============================================================
# STEP 7: TOP 10 FASTEST AND SLOWEST ROUTES
# ============================================================
top_routes = route_summary.nsmallest(10, "Average Lead Time")
print("\n=== TOP 10 FASTEST ROUTES ===")
print(top_routes[["Route", "Average Lead Time", "Total Orders"]])

worst_routes = route_summary.nlargest(10, "Average Lead Time")
print("\n=== WORST 10 SLOWEST ROUTES ===")
print(worst_routes[["Route", "Average Lead Time", "Total Orders"]])

# ============================================================
# STEP 8: DELAY ANALYSIS
# "Delayed" = fell into SLOW cluster (lead time > 1400 days)
# Only on routes with 10+ orders
# ============================================================
df["Delayed"] = df["Lead Time"] > 1400

delay_summary = df.groupby("Route").agg(
    Delayed=("Delayed", "mean"),
    Total_Orders=("Delayed", "count")
).reset_index()
delay_summary["Delay %"] = delay_summary["Delayed"] * 100

# *** KEY FIX: Filter to routes with 10+ orders ***
delay_summary = delay_summary[delay_summary["Total_Orders"] >= 10]

print("\n=== TOP 10 MOST DELAYED ROUTES (10+ orders only) ===")
worst_delay = delay_summary.nlargest(10, "Delay %")
print(worst_delay[["Route", "Total_Orders", "Delay %"]])

# ============================================================
# STEP 9: CHART 1 — Top 10 Most Delayed Routes
# ============================================================
top_delay = delay_summary.nlargest(10, "Delay %")

plt.figure(figsize=(13, 7))
colors = ["#d62728" if v > 50 else "#ff7f0e" if v > 30 else "#1f77b4"
          for v in top_delay["Delay %"]]
bars = plt.barh(top_delay["Route"], top_delay["Delay %"], color=colors)

for bar, val in zip(bars, top_delay["Delay %"]):
    plt.text(bar.get_width() + 0.5,
             bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}%", va="center", fontsize=10, fontweight="bold")

plt.xlabel("Delay % (% of orders that were slow)", fontsize=12)
plt.ylabel("Route (Factory → State)", fontsize=12)
plt.title("Top 10 Most Delayed Routes\n(Routes with 10+ orders only)", fontsize=14)
plt.xlim(0, 80)
plt.tight_layout()
plt.savefig("delayed_routes.png", dpi=150)
plt.show()
print("Chart 1 saved as delayed_routes.png")

# ============================================================
# STEP 10: CHART 2 — Top 10 Fastest Routes
# ============================================================
plt.figure(figsize=(13, 7))
bars2 = plt.barh(
    top_routes["Route"],
    top_routes["Average Lead Time"],
    color="green"
)

for bar, val in zip(bars2, top_routes["Average Lead Time"]):
    plt.text(bar.get_width() + 1,
             bar.get_y() + bar.get_height() / 2,
             f"{val:.0f} days", va="center", fontsize=10, fontweight="bold")

plt.xlabel("Average Lead Time (days)", fontsize=12)
plt.ylabel("Route (Factory → State)", fontsize=12)
plt.title("Top 10 Fastest Routes\n(Routes with 10+ orders only)", fontsize=14)
plt.tight_layout()
plt.savefig("fastest_routes.png", dpi=150)
plt.show()
print("Chart 2 saved as fastest_routes.png")

print("\n✅ Done! Both charts saved as PNG files in your project folder.")
delay_summary.to_excel("delay_summary.xlsx", index=False)
route_summary.to_excel("route_summary.xlsx", index=False)
