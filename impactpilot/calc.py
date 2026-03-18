"""Deterministic calculations for TCO and productivity using range midpoints."""


def compute_tco_from_ranges(
    tco_ranges: dict,
    hourly_rate: float = 100.0,
    horizon_years: int = 3
) -> dict:
    """
    Compute TCO metrics from assumption ranges using midpoints.
    
    Args:
        tco_ranges: Dict with build_person_days and run_person_days_per_year (each with range_min/max)
        hourly_rate: Hourly rate for cost calculations (default $100/hr)
        horizon_years: Time horizon for TCO calculation (default 3 years)
    
    Returns:
        Dict with computed TCO metrics using midpoint values
    """
    # Extract ranges
    build_days_min = tco_ranges.get("build_person_days", {}).get("range_min", 0)
    build_days_max = tco_ranges.get("build_person_days", {}).get("range_max", 0)
    
    run_days_min = tco_ranges.get("run_person_days_per_year", {}).get("range_min", 0)
    run_days_max = tco_ranges.get("run_person_days_per_year", {}).get("range_max", 0)
    
    # Compute midpoints
    build_days_mid = (build_days_min + build_days_max) / 2
    run_days_mid = (run_days_min + run_days_max) / 2
    
    # Convert to costs (8 hours per person-day)
    hours_per_day = 8
    
    build_cost = build_days_mid * hours_per_day * hourly_rate
    run_cost_per_year = run_days_mid * hours_per_day * hourly_rate
    total_run_cost = run_cost_per_year * horizon_years
    
    total_tco = build_cost + total_run_cost
    
    return {
        "build_person_days_midpoint": build_days_mid,
        "run_person_days_per_year_midpoint": run_days_mid,
        "build_cost_usd": build_cost,
        "run_cost_per_year_usd": run_cost_per_year,
        "total_run_cost_usd": total_run_cost,
        "total_tco_usd": total_tco,
        "horizon_years": horizon_years,
        "hourly_rate": hourly_rate,
    }


def compute_productivity_from_ranges(
    prod_ranges: dict,
    hourly_rate: float = 100.0,
    horizon_years: int = 3
) -> dict:
    """
    Compute productivity metrics from assumption ranges using midpoints.
    
    Args:
        prod_ranges: Dict with time_saved_hours_per_month and cost_avoided_per_year (each with range_min/max)
        hourly_rate: Hourly rate for cost calculations (default $100/hr)
        horizon_years: Time horizon for productivity calculation (default 3 years)
    
    Returns:
        Dict with computed productivity metrics using midpoint values
    """
    # Extract ranges
    time_saved_min = prod_ranges.get("time_saved_hours_per_month", {}).get("range_min", 0)
    time_saved_max = prod_ranges.get("time_saved_hours_per_month", {}).get("range_max", 0)
    
    cost_avoided_min = prod_ranges.get("cost_avoided_per_year", {}).get("range_min", 0)
    cost_avoided_max = prod_ranges.get("cost_avoided_per_year", {}).get("range_max", 0)
    
    # Compute midpoints
    time_saved_mid = (time_saved_min + time_saved_max) / 2
    cost_avoided_mid = (cost_avoided_min + cost_avoided_max) / 2
    
    # Annual calculations
    months_per_year = 12
    time_saved_per_year = time_saved_mid * months_per_year
    time_value_per_year = time_saved_per_year * hourly_rate
    
    total_time_saved = time_saved_per_year * horizon_years
    total_time_value = time_value_per_year * horizon_years
    total_cost_avoided = cost_avoided_mid * horizon_years
    
    total_productivity_gain = total_time_value + total_cost_avoided
    
    return {
        "time_saved_hours_per_month_midpoint": time_saved_mid,
        "cost_avoided_per_year_midpoint": cost_avoided_mid,
        "time_saved_hours_per_year": time_saved_per_year,
        "time_value_per_year_usd": time_value_per_year,
        "total_time_saved_hours": total_time_saved,
        "total_time_value_usd": total_time_value,
        "total_cost_avoided_usd": total_cost_avoided,
        "total_productivity_gain_usd": total_productivity_gain,
        "horizon_years": horizon_years,
        "hourly_rate": hourly_rate,
    }
