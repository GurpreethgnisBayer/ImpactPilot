"""Test calculator functions."""

from impactpilot.calc import compute_tco_from_ranges, compute_productivity_from_ranges


def test_tco_midpoint_computation():
    """Test that TCO computation uses midpoints correctly."""
    tco_ranges = {
        "build_person_days": {
            "range_min": 30,
            "range_max": 60
        },
        "run_person_days_per_year": {
            "range_min": 10,
            "range_max": 20
        }
    }
    
    result = compute_tco_from_ranges(tco_ranges, hourly_rate=100, horizon_years=3)
    
    # Check midpoints
    assert result["build_person_days_midpoint"] == 45.0  # (30+60)/2
    assert result["run_person_days_per_year_midpoint"] == 15.0  # (10+20)/2
    
    # Check build cost: 45 days * 8 hours/day * $100/hour
    assert result["build_cost_usd"] == 36000.0
    
    # Check run cost per year: 15 days * 8 hours/day * $100/hour
    assert result["run_cost_per_year_usd"] == 12000.0
    
    # Check total run cost: 12000 * 3 years
    assert result["total_run_cost_usd"] == 36000.0
    
    # Check total TCO: 36000 + 36000
    assert result["total_tco_usd"] == 72000.0


def test_productivity_midpoint_computation():
    """Test that productivity computation uses midpoints correctly."""
    prod_ranges = {
        "time_saved_hours_per_month": {
            "range_min": 10,
            "range_max": 20
        },
        "cost_avoided_per_year": {
            "range_min": 1000,
            "range_max": 5000
        }
    }
    
    result = compute_productivity_from_ranges(prod_ranges, hourly_rate=100, horizon_years=3)
    
    # Check midpoints
    assert result["time_saved_hours_per_month_midpoint"] == 15.0  # (10+20)/2
    assert result["cost_avoided_per_year_midpoint"] == 3000.0  # (1000+5000)/2
    
    # Check annual time saved: 15 hours/month * 12 months
    assert result["time_saved_hours_per_year"] == 180.0
    
    # Check time value per year: 180 hours * $100/hour
    assert result["time_value_per_year_usd"] == 18000.0
    
    # Check total time saved: 180 * 3 years
    assert result["total_time_saved_hours"] == 540.0
    
    # Check total time value: 18000 * 3 years
    assert result["total_time_value_usd"] == 54000.0
    
    # Check total cost avoided: 3000 * 3 years
    assert result["total_cost_avoided_usd"] == 9000.0
    
    # Check total productivity gain: 54000 + 9000
    assert result["total_productivity_gain_usd"] == 63000.0


def test_tco_with_different_rate():
    """Test TCO computation with different hourly rate."""
    tco_ranges = {
        "build_person_days": {
            "range_min": 20,
            "range_max": 40
        },
        "run_person_days_per_year": {
            "range_min": 5,
            "range_max": 15
        }
    }
    
    result = compute_tco_from_ranges(tco_ranges, hourly_rate=150, horizon_years=2)
    
    # Midpoint: 30 days * 8 hours * $150
    assert result["build_cost_usd"] == 36000.0
    
    # Midpoint: 10 days * 8 hours * $150
    assert result["run_cost_per_year_usd"] == 12000.0
    
    # 12000 * 2 years
    assert result["total_run_cost_usd"] == 24000.0
    
    # Total TCO
    assert result["total_tco_usd"] == 60000.0


def test_productivity_with_different_rate():
    """Test productivity computation with different hourly rate."""
    prod_ranges = {
        "time_saved_hours_per_month": {
            "range_min": 5,
            "range_max": 15
        },
        "cost_avoided_per_year": {
            "range_min": 2000,
            "range_max": 4000
        }
    }
    
    result = compute_productivity_from_ranges(prod_ranges, hourly_rate=150, horizon_years=2)
    
    # Midpoint: 10 hours/month
    assert result["time_saved_hours_per_month_midpoint"] == 10.0
    
    # 10 * 12 = 120 hours/year
    assert result["time_saved_hours_per_year"] == 120.0
    
    # 120 * $150
    assert result["time_value_per_year_usd"] == 18000.0
    
    # Midpoint: 3000/year
    assert result["cost_avoided_per_year_midpoint"] == 3000.0
    
    # Total productivity: (18000 + 3000) * 2
    assert result["total_productivity_gain_usd"] == 42000.0


def test_zero_ranges():
    """Test handling of zero ranges."""
    tco_ranges = {
        "build_person_days": {
            "range_min": 0,
            "range_max": 0
        },
        "run_person_days_per_year": {
            "range_min": 0,
            "range_max": 0
        }
    }
    
    result = compute_tco_from_ranges(tco_ranges)
    
    assert result["build_person_days_midpoint"] == 0.0
    assert result["run_person_days_per_year_midpoint"] == 0.0
    assert result["total_tco_usd"] == 0.0


def test_single_value_range():
    """Test when min equals max (single value)."""
    tco_ranges = {
        "build_person_days": {
            "range_min": 50,
            "range_max": 50
        },
        "run_person_days_per_year": {
            "range_min": 10,
            "range_max": 10
        }
    }
    
    result = compute_tco_from_ranges(tco_ranges, hourly_rate=100, horizon_years=1)
    
    # Midpoint should equal the value
    assert result["build_person_days_midpoint"] == 50.0
    assert result["run_person_days_per_year_midpoint"] == 10.0
    
    # 50 * 8 * 100
    assert result["build_cost_usd"] == 40000.0
    
    # 10 * 8 * 100
    assert result["run_cost_per_year_usd"] == 8000.0
    
    # Total: 40000 + 8000
    assert result["total_tco_usd"] == 48000.0
