# metrics.py

import numpy as np
from collections import Counter

# =============================
# 1️⃣ JAIN'S FAIRNESS INDEX
# =============================
def jains_fairness_index(allocations):
    allocations = np.array(allocations)

    if np.sum(allocations) == 0:
        return 0

    numerator = (np.sum(allocations)) ** 2
    denominator = len(allocations) * np.sum(allocations ** 2)

    return numerator / denominator


# =============================
# 2️⃣ WEIGHTED SLA VIOLATIONS
# =============================
def weighted_sla_violations(df, sla_threshold=2.0):
    """
    df must contain:
    - Response_Time
    - SLA (weight)
    """
    violations = df[df["Response_Time"] > sla_threshold]

    return (violations["SLA"]).sum()


# =============================
# 3️⃣ CPU-MEMORY CORRELATION
# =============================
def cpu_memory_correlation(df):
    """
    Validates co-allocation property
    Expected: High correlation (> 0.9)
    """

    cpu = df["CPU_Allocated"]
    memory = df["Memory_Allocated"]

    if len(cpu) < 2:
        return 0

    return np.corrcoef(cpu, memory)[0, 1]


# =============================
# 4️⃣ URGENCY TIER DISTRIBUTION
# =============================
def urgency_distribution(df):
    """
    Returns count of:
    critical / standard / background
    """

    tiers = df["Urgency_Tier"].dropna()

    return Counter(tiers)


# =============================
# 5️⃣ TOKEN VERIFICATION RATE
# =============================
def token_verification_rate(df):
    """
    In simulation → assume all tokens valid
    (since we generated them internally)

    For realism → check non-null tokens
    """

    total = len(df)

    valid = df["Bid_Token_Hash"].notnull().sum()

    if total == 0:
        return 0

    return valid / total


# =============================
# 6️⃣ UTILITY EFFICIENCY
# =============================
def utility_efficiency(df):
    """
    Utility = SLA_weight / response_time
    Higher = better
    """

    valid = df[df["Response_Time"] > 0]

    utility = (valid["SLA"] / valid["Response_Time"]).mean()

    return utility