"""
Quick validation script for TIG metrics
No pytest overhead - just direct fabric initialization and metrics check
"""

from __future__ import annotations


import asyncio
import sys

from maximus_core_service.consciousness.tig.fabric import TIGFabric, TopologyConfig


async def validate_tig_metrics():
    logger.info("=" * 60)
    logger.info("TIG METRICS VALIDATION - PAGANI 100%")
    logger.info("=" * 60)
    print()

    # Initialize fabric with default config
    config = TopologyConfig(node_count=16, min_degree=6)
    fabric = TIGFabric(config)

    logger.info("Initializing TIG Fabric...")
    await fabric.initialize()

    # Get metrics
    metrics = fabric.get_metrics()

    print()
    logger.info("📊 METRICS RESULTS:")
    print("-" * 60)
    logger.info("Clustering Coefficient: %.3f (target: ≥0.70)", metrics.avg_clustering_coefficient)
    logger.info("ECI (Φ Proxy):          %.3f (target: ≥0.85)", metrics.effective_connectivity_index)
    logger.info("Avg Path Length:        %.2f (target: ≤7)", metrics.avg_path_length)
    logger.info("Algebraic Connectivity: %.3f (target: ≥0.30)", metrics.algebraic_connectivity)
    logger.info(
        f"Bottlenecks:            {'YES ❌' if metrics.has_feed_forward_bottlenecks else 'NO ✅'}"
    )
    logger.info("Graph Density:          %.3f", metrics.density)
    print()

    # Validate IIT compliance
    is_compliant, violations = metrics.validate_iit_compliance()

    logger.info("🎯 IIT COMPLIANCE:")
    print("-" * 60)
    if is_compliant:
        logger.info("✅ ALL CHECKS PASSED - IIT COMPLIANT")
        print()
        logger.info("🏎️ PAGANI TARGET ACHIEVED!")
        return 0
    logger.info("❌ IIT VIOLATIONS DETECTED:")
    for v in violations:
        logger.info("   - %s", v)
    print()
    logger.info("Clustering: %s", '✅' if metrics.avg_clustering_coefficient >= 0.70 else '❌')
    logger.info("ECI:        %s", '✅' if metrics.effective_connectivity_index >= 0.85 else '❌')
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(validate_tig_metrics())
    sys.exit(exit_code)
