# simulation_runner.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from services import Microservice
from auction_engine import proportional_auction_huae
from baseline_allocator import priority_static_allocation

# =============================
# CONFIGURATION
# =============================
TOTAL_CPU = 150
TOTAL_MEMORY = 300   # NEW (important)
TIME_STEPS = 60
SLA_THRESHOLD = 2.0

# =============================
# INITIALIZE SERVICES
# =============================
def init_services():
    return [
        Microservice("S1", 1.0),
        Microservice("S2", 1.2),
        Microservice("S3", 0.8),
        Microservice("S4", 1.5),
        Microservice("S5", 1.0),
        Microservice("S6", 1.3),
    ]

services_auction = init_services()
services_baseline = init_services()

auction_results = []
baseline_results = []

# =============================
# SIMULATION LOOP
# =============================
for t in range(TIME_STEPS):

    # -------- LOAD GENERATION --------
    for s_a, s_b in zip(services_auction, services_baseline):

        if 20 <= t <= 35:
            if s_a.service_id == "S4":
                load = np.random.randint(150, 220)
            elif s_a.service_id == "S2":
                load = np.random.randint(100, 160)
            else:
                load = np.random.randint(50, 120)
        else:
            load = np.random.randint(20, 80)

        s_a.current_load = load
        s_b.current_load = load

    # =============================
    # AUCTION (HUAE)
    # =============================
    for s in services_auction:
        s.calculate_response_time()
        s.compute_bid(SLA_THRESHOLD)

    proportional_auction_huae(services_auction, TOTAL_CPU, TOTAL_MEMORY)

    for s in services_auction:

        rt = s.calculate_response_time()

        auction_results.append({
            "Time": t,
            "ServiceID": s.service_id,
            "Strategy": "Auction",
            "Load": s.current_load,
            "CPU_Bid": s.cpu_bid,
            "Memory_Bid": s.memory_bid,
            "Urgency_Tier": s.urgency_tier,
            "Bid_Token_Hash": s.bid_token,
            "CPU_Allocated": s.allocated_cpu,
            "Memory_Allocated": s.allocated_memory,
            "Response_Time": rt,
            "SLA": s.sla_weight
        })

    # =============================
    # BASELINE
    # =============================
    priority_static_allocation(services_baseline, TOTAL_CPU, TOTAL_MEMORY)

    for s in services_baseline:

        rt = s.calculate_response_time()

        baseline_results.append({
            "Time": t,
            "ServiceID": s.service_id,
            "Strategy": "Baseline",
            "Load": s.current_load,
            "CPU_Bid": None,
            "Memory_Bid": None,
            "Urgency_Tier": None,
            "Bid_Token_Hash": None,
            "CPU_Allocated": s.allocated_cpu,
            "Memory_Allocated": s.allocated_memory,
            "Response_Time": rt,
            "SLA": s.sla_weight
        })

# =============================
# DATAFRAME + CSV
# =============================
df_all = pd.DataFrame(auction_results + baseline_results)
df_all.to_csv("comparison_results.csv", index=False)

print("CSV saved: comparison_results.csv")

# =============================
# METRICS
# =============================

# Average Response Time
avg_rt = df_all.groupby(["Time","Strategy"])["Response_Time"].mean().unstack()

# =============================
# VISUALIZATION 1
# =============================
plt.figure()
plt.plot(avg_rt["Auction"], label="Auction")
plt.plot(avg_rt["Baseline"], label="Baseline")
plt.title("Average Response Time Comparison")
plt.xlabel("Time")
plt.ylabel("Response Time")
plt.legend(loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig("1_avg_response_time.png")
plt.show()

# =============================
# VISUALIZATION 2 (CPU Allocation)
# =============================
plt.figure()
for sid in df_all["ServiceID"].unique():
    subset = df_all[(df_all["ServiceID"]==sid) & (df_all["Strategy"]=="Auction")]
    plt.plot(subset["Time"], subset["CPU_Allocated"], label=sid)

plt.title("CPU Allocation (Auction)")
plt.legend(loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig("2_cpu_allocation.png")
plt.show()

# =============================
# VISUALIZATION 3 (Memory Allocation)
# =============================
plt.figure()
for sid in df_all["ServiceID"].unique():
    subset = df_all[(df_all["ServiceID"]==sid) & (df_all["Strategy"]=="Auction")]
    plt.plot(subset["Time"], subset["Memory_Allocated"], label=sid)

plt.title("Memory Allocation (Auction)")
plt.legend(loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig("3_memory_allocation.png")
plt.show()

# =============================
# VISUALIZATION 4 (Urgency Distribution)
# =============================
\

import seaborn as sns

auction_df = df_all[df_all["Strategy"]=="Auction"]

plt.figure()
sns.countplot(data=auction_df, x="Urgency_Tier")
plt.title("Urgency Tier Distribution")
plt.savefig("4_urgency_distribution.png")
plt.show()

# =============================
# VISUALIZATION 5 (Bid Trends)
# =============================
plt.figure()
for sid in auction_df["ServiceID"].unique():
    subset = auction_df[auction_df["ServiceID"]==sid]
    plt.plot(subset["Time"], subset["CPU_Bid"], label=sid)

plt.title("CPU Bid Evolution")
plt.legend(loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig("5_bid_evolution.png")
plt.show()

from metrics import *

auction_df = df_all[df_all["Strategy"]=="Auction"]

print("\n===== FINAL METRICS =====")

# 1. Resource Utilization
cpu_util = auction_df.groupby("Time")["CPU_Allocated"].sum() / TOTAL_CPU
print("Resource Utilization:", cpu_util.mean())

# 2. Weighted SLA Violations
violations = auction_df[auction_df["Response_Time"] > SLA_THRESHOLD]
print("Weighted SLA Violations:", violations["SLA"].sum())

# 3. Fairness
print("Jain Fairness:", jains_fairness_index(auction_df["CPU_Allocated"]))

# 4. Average Response Time
print("Average Response Time:", auction_df["Response_Time"].mean())

# 5. Starvation
auction_df["Starved"] = auction_df["CPU_Allocated"] < 0.2 * auction_df["Load"]
print("Starvation Incidents:", auction_df["Starved"].sum())

# 6. Urgency Distribution
print("Urgency Distribution:", urgency_distribution(auction_df))

# 7. CPU-Memory Correlation
print("CPU-Memory Correlation:", cpu_memory_correlation(auction_df))

# 8. Token Verification Rate
print("Token Verification Rate:", token_verification_rate(auction_df))

# 9. Utility Efficiency
print("Utility Efficiency:", utility_efficiency(auction_df))

auction_df = df_all[df_all["Strategy"]=="Auction"]

# =============================
# SPIKE RECOVERY ANALYSIS
# =============================

avg_rt_auction = df_all[df_all["Strategy"]=="Auction"].groupby("Time")["Response_Time"].mean()
avg_rt_baseline = df_all[df_all["Strategy"]=="Baseline"].groupby("Time")["Response_Time"].mean()

plt.figure()
plt.plot(avg_rt_auction, label="Auction")
plt.plot(avg_rt_baseline, label="Baseline")

# Mark spike window
plt.axvline(x=20, linestyle="--")
plt.axvline(x=35, linestyle="--")

plt.title("Spike Window & Recovery Analysis")
plt.xlabel("Time")
plt.ylabel("Response Time")
plt.legend()

plt.savefig("15_spike_recovery.png")
plt.show()

# =============================
# CDF OF RESPONSE TIMES
# =============================

auction_rt = df_all[df_all["Strategy"]=="Auction"]["Response_Time"]
baseline_rt = df_all[df_all["Strategy"]=="Baseline"]["Response_Time"]

sorted_auction = np.sort(auction_rt)
sorted_baseline = np.sort(baseline_rt)

cdf_auction = np.arange(len(sorted_auction)) / len(sorted_auction)
cdf_baseline = np.arange(len(sorted_baseline)) / len(sorted_baseline)

plt.figure()
plt.plot(sorted_auction, cdf_auction, label="Auction")
plt.plot(sorted_baseline, cdf_baseline, label="Baseline")

plt.title("CDF of Response Times")
plt.xlabel("Response Time")
plt.ylabel("Cumulative Probability")
plt.legend()

plt.savefig("18_cdf_response.png")
plt.show()

print("\n===== FINAL METRICS =====")

# 1. Resource Utilization
cpu_util = auction_df.groupby("Time")["CPU_Allocated"].sum() / TOTAL_CPU
print("Resource Utilization:", cpu_util.mean())

# 2. Weighted SLA Violations
violations = auction_df[auction_df["Response_Time"] > SLA_THRESHOLD]
print("Weighted SLA Violations:", violations["SLA"].sum())

# 3. Fairness
print("Jain Fairness:", jains_fairness_index(auction_df["CPU_Allocated"]))

# 4. Average Response Time
print("Average Response Time:", auction_df["Response_Time"].mean())

# 5. Starvation
auction_df["Starved"] = auction_df["CPU_Allocated"] < 0.2 * auction_df["Load"]
print("Starvation Incidents:", auction_df["Starved"].sum())

# 6. Urgency Distribution
print("Urgency Distribution:", urgency_distribution(auction_df))

# 7. CPU-Memory Correlation
print("CPU-Memory Correlation:", cpu_memory_correlation(auction_df))

# 8. Token Verification Rate
print("Token Verification Rate:", token_verification_rate(auction_df))

# 9. Utility Efficiency
print("Utility Efficiency:", utility_efficiency(auction_df))
print("All core graphs generated.")