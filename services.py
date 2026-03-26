
import numpy as np
import math
import hashlib
import hmac
import time

# =============================
# GLOBAL CONFIG
# =============================
SECRET_KEY = b"huge_secret_key_for_huae"


class Microservice:
    def __init__(self, service_id, sla_weight):
        self.service_id = service_id
        self.sla_weight = sla_weight

        # Runtime states
        self.current_load = 0
        self.allocated_cpu = 0
        self.allocated_memory = 0

        # Bid values (2D)
        self.cpu_bid = 5
        self.memory_bid = 5

        # Previous bids for smoothing
        self.prev_cpu_bid = 5
        self.prev_memory_bid = 5

        # SLA tracking
        self.response_time = 1
        self.urgency_tier = "background"

        # Budget constraint
        self.base_budget = 80

        # Token storage
        self.bid_token = None

    # =============================
    # 1️⃣ URGENCY CLASSIFICATION (UCE)
    # =============================
    def classify_urgency(self, sla_threshold):
        headroom = (sla_threshold - self.response_time) / sla_threshold
        headroom = max(-1, min(headroom, 1))

        if self.response_time > sla_threshold:
            self.urgency_tier = "critical"
        elif headroom < 0.2:
            self.urgency_tier = "standard"
        else:
            self.urgency_tier = "background"

        return self.urgency_tier

    # =============================
    # 2️⃣ SLA-DECAY CONTROLLER (SDFC)
    # =============================
    def sla_decay_multiplier(self, sla_threshold):
        headroom = (sla_threshold - self.response_time) / sla_threshold
        headroom = max(-1, min(headroom, 1))

        # Strong boost when SLA violated
        decay = np.exp(-headroom * 7)

        return decay

    # =============================
    # 3️⃣ BID COMPUTATION (2D)
    # =============================
    def compute_bid(self, sla_threshold):

        # Demand estimation
        overload = max(0, self.current_load - self.allocated_cpu)
        demand = math.log(1 + overload)

        # Urgency classification
        urgency = self.classify_urgency(sla_threshold)

        # Urgency multiplier
        if urgency == "critical":
            urgency_factor = 2.5

        elif urgency == "standard":
            urgency_factor = 1.3
        else:
            urgency_factor = 0.8

        # SLA decay boost
        decay = self.sla_decay_multiplier(sla_threshold)

        # Budget constraint
        max_budget = self.base_budget * self.sla_weight

        # CPU bid
        raw_cpu_bid = demand * (self.sla_weight**1.5) * urgency_factor * decay
        cpu_bid = min(max_budget, raw_cpu_bid)

        # Memory bid (correlated with CPU)
        raw_memory_bid = cpu_bid * np.random.uniform(0.95, 1.05)
        memory_bid = min(max_budget, raw_memory_bid)

        # Smoothing (to prevent oscillation)
        cpu_bid = 0.6 * self.prev_cpu_bid + 0.4 * cpu_bid
        memory_bid = 0.6 * self.prev_memory_bid + 0.4 * memory_bid

        self.cpu_bid = cpu_bid
        self.memory_bid = memory_bid

        self.prev_cpu_bid = cpu_bid
        self.prev_memory_bid = memory_bid

        # Generate cryptographic token
        self.bid_token = self.generate_bid_token()

        return self.cpu_bid, self.memory_bid

    # =============================
    # 4️⃣ CRYPTO BID TOKEN (CBTG)
    # =============================
    def generate_bid_token(self):
        nonce = str(time.time()).encode()

        message = f"{self.service_id}-{self.cpu_bid:.4f}-{self.memory_bid:.4f}".encode()

        token = hmac.new(
            SECRET_KEY,
            message + nonce,
            hashlib.sha256
        ).hexdigest()

        return token

    # =============================
    # 5️⃣ RESPONSE TIME MODEL
    # =============================
    def calculate_response_time(self):

        if self.allocated_cpu == 0:
            self.response_time = 100
            return self.response_time

        # If enough CPU
        if self.allocated_cpu >= self.current_load:
            self.response_time = 1 + (self.current_load / self.allocated_cpu)

        else:
            overload_ratio = self.current_load / self.allocated_cpu
            self.response_time = overload_ratio ** 1.5

        return self.response_time