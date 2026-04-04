"""
Lab 01 – Carbon Footprint Calculator
Estimates and compares CO2 emissions for Lambda vs EC2 compute.

Emission factors are approximations based on:
- AWS average grid carbon intensity: ~0.000120 kg CO2e/kWh (mixed US regions)
- Green regions (eu-west-1, us-west-2): ~0.000028 kg CO2e/kWh
- EC2 t3.micro TDP: ~4W (at typical utilisation)
- EC2 m5.large TDP: ~14W (at typical utilisation)
- Lambda: proportional energy based on GB-seconds consumed
"""

import json

# ── Emission constants ────────────────────────────────────────────────────────
# Carbon intensity in kg CO2e per kWh (AWS global average)
CARBON_INTENSITY_KG_PER_KWH = 0.000120

# Lambda energy efficiency: ~0.0000003 kWh per GB-second (NIST estimate)
LAMBDA_KWH_PER_GB_SECOND = 0.0000003

# EC2 instance power draw in Watts (at ~30% average CPU utilisation)
EC2_POWER_W = {
    "t3.micro": 4.0,
    "m5.large": 14.0,
}

# EC2 on-demand pricing USD/hour (us-east-1 approximation)
EC2_PRICE_USD_PER_HOUR = {
    "t3.micro": 0.0104,
    "m5.large": 0.096,
}

# Lambda pricing
LAMBDA_PRICE_PER_GB_SECOND = 0.0000166667
LAMBDA_PRICE_PER_REQUEST = 0.0000002
LAMBDA_FREE_TIER_GB_SECONDS = 400_000
LAMBDA_FREE_TIER_REQUESTS = 1_000_000

HOURS_PER_MONTH = 730


def calculate_lambda_footprint(invocations_per_day: int, avg_duration_ms: float, memory_mb: int) -> dict:
    """Calculate monthly Lambda cost and CO2 for the given workload."""
    monthly_invocations = invocations_per_day * 30
    duration_seconds = avg_duration_ms / 1000.0
    memory_gb = memory_mb / 1024.0

    # Compute GB-seconds consumed per month
    gb_seconds = monthly_invocations * duration_seconds * memory_gb

    # Energy in kWh
    energy_kwh = gb_seconds * LAMBDA_KWH_PER_GB_SECOND

    # CO2 in grams
    co2_grams = energy_kwh * CARBON_INTENSITY_KG_PER_KWH * 1000

    # Cost (simplified, ignoring free tier for clarity)
    cost_usd = (gb_seconds * LAMBDA_PRICE_PER_GB_SECOND) + (monthly_invocations * LAMBDA_PRICE_PER_REQUEST)

    return {
        "monthlyInvocations": monthly_invocations,
        "monthlyGbSeconds": round(gb_seconds, 2),
        "energyKwh": round(energy_kwh, 6),
        "estimatedCO2Grams": round(co2_grams, 6),
        "estimatedMonthlyCostUSD": round(cost_usd, 4),
    }


def calculate_ec2_footprint(instance_type: str) -> dict:
    """Calculate monthly EC2 cost and CO2 for a 24/7 running instance."""
    power_w = EC2_POWER_W[instance_type]
    price_per_hour = EC2_PRICE_USD_PER_HOUR[instance_type]

    # Energy in kWh (running 24/7)
    energy_kwh = (power_w / 1000.0) * HOURS_PER_MONTH

    # CO2 in grams
    co2_grams = energy_kwh * CARBON_INTENSITY_KG_PER_KWH * 1000

    # Cost
    cost_usd = price_per_hour * HOURS_PER_MONTH

    return {
        "monthlyHours": HOURS_PER_MONTH,
        "energyKwh": round(energy_kwh, 4),
        "estimatedCO2Grams": round(co2_grams, 2),
        "estimatedMonthlyCostUSD": round(cost_usd, 2),
    }


def handler(event: dict, context) -> dict:
    """
    Lambda handler – compares CO2 footprint of different compute options.

    Input event fields:
        invocationsPerDay  (int)   – number of Lambda invocations per day
        avgDurationMs      (float) – average Lambda execution duration in ms
        memorySizeMB       (int)   – Lambda memory allocation in MB
    """
    invocations_per_day = int(event.get("invocationsPerDay", 10_000))
    avg_duration_ms = float(event.get("avgDurationMs", 200))
    memory_mb = int(event.get("memorySizeMB", 512))

    lambda_stats = calculate_lambda_footprint(invocations_per_day, avg_duration_ms, memory_mb)
    t3_stats = calculate_ec2_footprint("t3.micro")
    m5_stats = calculate_ec2_footprint("m5.large")

    # Compute CO2 ratio for summary message
    lambda_co2 = lambda_stats["estimatedCO2Grams"]
    m5_co2 = m5_stats["estimatedCO2Grams"]
    ratio = round(m5_co2 / lambda_co2) if lambda_co2 > 0 else "N/A"

    summary = (
        f"Lambda emits ~{ratio}x less CO2 than an EC2 m5.large for this workload. "
        f"Lambda CO2: {lambda_co2}g/month vs m5.large: {m5_co2}g/month."
    )

    body = {
        "workload": {
            "invocationsPerDay": invocations_per_day,
            "avgDurationMs": avg_duration_ms,
            "memorySizeMB": memory_mb,
        },
        "comparison": {
            "lambda": lambda_stats,
            "ec2_t3micro_24x7": t3_stats,
            "ec2_m5large_24x7": m5_stats,
        },
        "summary": summary,
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, indent=2),
    }
