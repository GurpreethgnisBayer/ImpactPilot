"""Deterministic TCO and productivity calculations."""

from typing import Optional


def compute_tco(
    tco_inputs: dict,
    hourly_rate: float,
    horizon_years: int
) -> dict:
    """
    Compute Total Cost of Ownership over a horizon.
    
    RULE: If any required numeric input is None, returns None outputs with explanation.
    
    Args:
        tco_inputs: Dict with keys:
            - build_person_days: Person-days to build/implement (or None)
            - run_person_days_per_year: Person-days per year to operate (or None)
            - license_cost_per_year: Annual license costs (or None)
            - compute_cost_per_year: Annual compute/infrastructure costs (or None)
            - training_hours: One-time training hours (or None)
            - downtime_hours_per_year: Annual downtime/maintenance hours (or None)
        hourly_rate: Effective hourly cost rate
        horizon_years: Planning horizon in years
        
    Returns:
        Dict with horizon_cost, annual_run_cost, breakdown, explanation
    """
    # Extract inputs
    build_person_days = tco_inputs.get("build_person_days")
    run_person_days_per_year = tco_inputs.get("run_person_days_per_year")
    license_cost_per_year = tco_inputs.get("license_cost_per_year")
    compute_cost_per_year = tco_inputs.get("compute_cost_per_year")
    training_hours = tco_inputs.get("training_hours")
    downtime_hours_per_year = tco_inputs.get("downtime_hours_per_year")
    
    # Check if all required inputs are present
    required_inputs = [
        build_person_days,
        run_person_days_per_year,
        license_cost_per_year,
        compute_cost_per_year,
        training_hours,
        downtime_hours_per_year
    ]
    
    if any(inp is None for inp in required_inputs):
        return {
            "horizon_cost": None,
            "annual_run_cost": None,
            "breakdown": {},
            "explanation": "Insufficient evidence-derived inputs for TCO. Validate or provide inputs."
        }
    
    # Compute one-time costs
    build_cost_once = build_person_days * 8 * hourly_rate
    training_cost_once = training_hours * hourly_rate
    
    # Compute annual recurring costs
    labor_run_cost_per_year = run_person_days_per_year * 8 * hourly_rate
    downtime_cost_per_year = downtime_hours_per_year * hourly_rate
    annual_run_cost = (
        labor_run_cost_per_year +
        license_cost_per_year +
        compute_cost_per_year +
        downtime_cost_per_year
    )
    
    # Compute horizon total
    horizon_cost = build_cost_once + training_cost_once + horizon_years * annual_run_cost
    
    return {
        "horizon_cost": horizon_cost,
        "annual_run_cost": annual_run_cost,
        "breakdown": {
            "build_cost_once": build_cost_once,
            "training_cost_once": training_cost_once,
            "license_cost_per_year": license_cost_per_year,
            "compute_cost_per_year": compute_cost_per_year,
            "downtime_cost_per_year": downtime_cost_per_year,
            "labor_run_cost_per_year": labor_run_cost_per_year
        },
        "explanation": ""
    }


def compute_productivity(
    prod_inputs: dict,
    hourly_rate: float,
    horizon_years: int
) -> dict:
    """
    Compute productivity impact over a horizon.
    
    RULE: If time_saved_hours_per_month AND cost_avoided_per_year are both None,
    returns None outputs with explanation.
    
    Args:
        prod_inputs: Dict with keys:
            - time_saved_hours_per_month: Monthly time savings (or None)
            - cost_avoided_per_year: Annual cost avoidance (or None)
            - throughput_delta_per_year: Annual throughput change (or None, directional)
            - success_prob_delta: Success probability change (or None, directional)
        hourly_rate: Effective hourly value rate
        horizon_years: Planning horizon in years
        
    Returns:
        Dict with horizon_productivity_value, annual_productivity_value, breakdown, explanation
    """
    # Extract inputs
    time_saved_hours_per_month = prod_inputs.get("time_saved_hours_per_month")
    cost_avoided_per_year = prod_inputs.get("cost_avoided_per_year")
    throughput_delta_per_year = prod_inputs.get("throughput_delta_per_year")
    success_prob_delta = prod_inputs.get("success_prob_delta")
    
    # Check if we have at least one primary input
    if time_saved_hours_per_month is None and cost_avoided_per_year is None:
        return {
            "horizon_productivity_value": None,
            "annual_productivity_value": None,
            "breakdown": {},
            "throughput_delta_per_year": throughput_delta_per_year,
            "success_prob_delta": success_prob_delta,
            "explanation": "Insufficient evidence-derived inputs for productivity. Validate or provide inputs."
        }
    
    # Compute time value
    annual_hours_saved = (time_saved_hours_per_month or 0) * 12
    annual_time_value = annual_hours_saved * hourly_rate
    
    # Compute total annual productivity value
    annual_productivity_value = annual_time_value + (cost_avoided_per_year or 0)
    
    # Compute horizon total
    horizon_productivity_value = horizon_years * annual_productivity_value
    
    return {
        "horizon_productivity_value": horizon_productivity_value,
        "annual_productivity_value": annual_productivity_value,
        "breakdown": {
            "annual_hours_saved": annual_hours_saved,
            "annual_time_value": annual_time_value,
            "cost_avoided_per_year": cost_avoided_per_year or 0
        },
        "throughput_delta_per_year": throughput_delta_per_year,
        "success_prob_delta": success_prob_delta,
        "explanation": ""
    }
