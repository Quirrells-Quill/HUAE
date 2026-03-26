

def priority_static_allocation(services, total_cpu, total_memory):
    """
    Static baseline allocation:
    - Based only on SLA weights
    - No bidding, no urgency, no adaptation
    - Allocates BOTH CPU and Memory proportionally
    """

    total_weight = sum(service.sla_weight for service in services)

    if total_weight == 0:
        return

    for service in services:

        # CPU allocation
        cpu_share = (service.sla_weight / total_weight) * total_cpu * 0.95
        service.allocated_cpu = cpu_share

        # Memory allocation (same proportion)
        memory_share = (service.sla_weight / total_weight) * total_memory * 0.95
        service.allocated_memory = memory_share