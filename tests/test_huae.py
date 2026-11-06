# tests/test_huae.py
"""
Comprehensive automated test suite for the Holistic Urgency-Aware Auction Engine (HUAE).
Validates urgency classification, SLA feedback decay, cryptographic bid tokens,
multi-resource co-allocation conservation, and analytical metrics.
"""

import math
import numpy as np
import pytest

from services import Microservice, SECRET_KEY
from auction_engine import proportional_auction_huae, verify_bid_token
from baseline_allocator import priority_static_allocation
from metrics import (
    jains_fairness_index,
    weighted_sla_violations,
    cpu_memory_correlation,
    urgency_distribution,
    token_verification_rate,
    utility_efficiency,
)
import pandas as pd


class TestUrgencyClassification:
    """Validates the Urgency Classification Engine (UCE)."""

    def test_critical_tier_when_violating_sla(self):
        s = Microservice("S_crit", sla_weight=1.0)
        s.response_time = 3.5
        tier = s.classify_urgency(sla_threshold=2.0)
        assert tier == "critical"

    def test_standard_tier_when_near_sla_threshold(self):
        s = Microservice("S_std", sla_weight=1.0)
        # headroom = (2.0 - 1.8) / 2.0 = 0.1 < 0.2
        s.response_time = 1.8
        tier = s.classify_urgency(sla_threshold=2.0)
        assert tier == "standard"

    def test_background_tier_when_healthy(self):
        s = Microservice("S_bg", sla_weight=1.0)
        # headroom = (2.0 - 1.0) / 2.0 = 0.5 >= 0.2
        s.response_time = 1.0
        tier = s.classify_urgency(sla_threshold=2.0)
        assert tier == "background"


class TestSLADecayMultiplier:
    """Validates the SLA-Decay Feedback Controller (SDFC)."""

    def test_decay_increases_monotonically_with_sla_violation(self):
        s = Microservice("S_decay", sla_weight=1.0)
        s.response_time = 1.0
        decay_healthy = s.sla_decay_multiplier(sla_threshold=2.0)

        s.response_time = 2.5
        decay_violated = s.sla_decay_multiplier(sla_threshold=2.0)

        assert decay_violated > decay_healthy


class TestBidComputationAndCryptoTokens:
    """Validates 2D bid generation, budget capping, and CBTG tokens."""

    def test_bids_respect_budget_cap(self):
        s = Microservice("S_budget", sla_weight=1.2)
        s.current_load = 500
        s.allocated_cpu = 10
        s.response_time = 5.0

        cpu_bid, mem_bid = s.compute_bid(sla_threshold=2.0)
        max_budget = s.base_budget * s.sla_weight

        assert cpu_bid <= max_budget
        assert mem_bid <= max_budget

    def test_token_generated_is_valid_sha256(self):
        s = Microservice("S_token", sla_weight=1.0)
        s.compute_bid(sla_threshold=2.0)
        assert s.bid_token is not None
        assert len(s.bid_token) == 64  # SHA-256 hex digest length
        assert verify_bid_token(s) is True

    def test_verify_rejects_missing_token(self):
        s = Microservice("S_notoken", sla_weight=1.0)
        s.bid_token = None
        assert verify_bid_token(s) is False


class TestProportionalAuction:
    """Validates the joint CPU-memory proportional auction engine."""

    def test_auction_co_allocation_conservation(self):
        services = [
            Microservice("S1", 1.0),
            Microservice("S2", 1.5),
            Microservice("S3", 0.8),
        ]
        for s in services:
            s.current_load = 50
            s.allocated_cpu = 20
            s.compute_bid(sla_threshold=2.0)

        total_cpu = 150.0
        total_memory = 300.0
        proportional_auction_huae(services, total_cpu, total_memory)

        allocated_cpu_sum = sum(s.allocated_cpu for s in services)
        allocated_mem_sum = sum(s.allocated_memory for s in services)

        assert math.isclose(allocated_cpu_sum, total_cpu, rel_tol=1e-5)
        assert math.isclose(allocated_mem_sum, total_memory, rel_tol=1e-5)

    def test_auction_skips_invalid_tokens(self):
        s1 = Microservice("S1", 1.0)
        s2 = Microservice("S2", 1.0)
        s1.compute_bid(sla_threshold=2.0)
        s2.compute_bid(sla_threshold=2.0)
        s2.bid_token = None  # Invalidate token

        proportional_auction_huae([s1, s2], total_cpu=100.0, total_memory=200.0)
        assert s1.allocated_cpu == 100.0
        assert s2.allocated_cpu == 0.0


class TestBaselineAllocator:
    """Validates static SLA-weighted baseline allocation."""

    def test_static_allocation_proportional_to_weight(self):
        s1 = Microservice("S1", 1.0)
        s2 = Microservice("S2", 2.0)
        priority_static_allocation([s1, s2], total_cpu=100.0, total_memory=200.0)

        # Total weight = 3.0. Shares have 0.95 factor:
        # s1: (1/3) * 100 * 0.95 = 31.666...
        # s2: (2/3) * 100 * 0.95 = 63.333...
        assert math.isclose(s1.allocated_cpu * 2, s2.allocated_cpu, rel_tol=1e-5)
        assert math.isclose(s1.allocated_memory * 2, s2.allocated_memory, rel_tol=1e-5)


class TestMetrics:
    """Validates analytical benchmarking metrics."""

    def test_jains_fairness_index(self):
        # Equal allocations -> perfect fairness (1.0)
        assert math.isclose(jains_fairness_index([10, 10, 10, 10]), 1.0)
        # Empty / zero allocation -> 0
        assert jains_fairness_index([0, 0, 0]) == 0
        # Unequal allocations -> < 1.0
        assert jains_fairness_index([10, 50, 100]) < 1.0

    def test_cpu_memory_correlation(self):
        df = pd.DataFrame({
            "CPU_Allocated": [10.0, 20.0, 30.0, 40.0],
            "Memory_Allocated": [20.0, 40.0, 60.0, 80.0],
        })
        corr = cpu_memory_correlation(df)
        assert math.isclose(corr, 1.0, rel_tol=1e-4)

    def test_weighted_sla_violations(self):
        df = pd.DataFrame({
            "Response_Time": [1.2, 2.5, 3.1],
            "SLA": [1.0, 1.5, 2.0],
        })
        violations = weighted_sla_violations(df, sla_threshold=2.0)
        # Only row 1 (1.5) and row 2 (2.0) are > 2.0
        assert violations == 3.5

    def test_token_verification_rate(self):
        df = pd.DataFrame({
            "Bid_Token_Hash": ["token_a", "token_b", None],
        })
        rate = token_verification_rate(df)
        assert math.isclose(rate, 2 / 3, rel_tol=1e-4)
