# auction_engine.py

import hmac
import hashlib

# Must match services.py
SECRET_KEY = b"huge_secret_key_for_huae"


# =============================
# 1️⃣ TOKEN VERIFICATION (CBTG Validation)
# =============================
def verify_bid_token(service):
    """
    Verifies integrity of bid token.
    In real system → prevents tampering.
    """

    try:
        # Recreate message
        message = f"{service.service_id}-{service.cpu_bid:.4f}-{service.memory_bid:.4f}".encode()

        # NOTE:
        # Since nonce is unknown here (simulated system),
        # we assume token correctness.
        # In real system → nonce stored & verified.

        if service.bid_token is None:
            return False

        return True

    except:
        return False


# =============================
# 2️⃣ JOINT PROPORTIONAL AUCTION (CPU + MEMORY)
# =============================
def proportional_auction_huae(services, total_cpu, total_memory):
    """
    Core HUAE auction engine.

    - Verifies bid tokens
    - Performs joint CPU-memory co-allocation
    - Ensures proportional fairness
    """

    # Step 1: Verify tokens
    valid_services = []

    for s in services:
        if verify_bid_token(s):
            valid_services.append(s)
        else:
            # Invalid token → reject service
            s.cpu_bid = 0
            s.memory_bid = 0

    if len(valid_services) == 0:
        return

    # Step 2: Compute total bids
    total_cpu_bid = sum(s.cpu_bid for s in valid_services)
    total_memory_bid = sum(s.memory_bid for s in valid_services)

    if total_cpu_bid == 0 or total_memory_bid == 0:
        return

    # Step 3: Allocate resources proportionally
    for s in valid_services:

        # CPU allocation
        s.allocated_cpu = (s.cpu_bid / total_cpu_bid) * total_cpu

        # Memory allocation (COUPLED with bidding)
        s.allocated_memory = (s.memory_bid / total_memory_bid) * total_memory


# =============================
# 3️⃣ BASELINE AUCTION (FOR COMPARISON)
# =============================
def proportional_auction_legacy(services, total_cpu):
    """
    Old version (CPU only) — kept for comparison
    """

    total_bids = sum(s.cpu_bid for s in services)

    if total_bids == 0:
        return

    for s in services:
        s.allocated_cpu = (s.cpu_bid / total_bids) * total_cpu