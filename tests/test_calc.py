"""Tests for TCO and productivity calculations."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.calc import compute_tco, compute_productivity


def test_compute_tco_with_missing_inputs():
    """Test that compute_tco returns None outputs when inputs are missing."""
    tco_inputs = {
        "build_person_days": 10,
        "run_person_days_per_year": None,  # Missing
        "license_cost_per_year": 5000,
        "compute_cost_per_year": 2000,
        "training_hours": 40,
        "downtime_hours_per_year": 10
    }
    
    result = compute_tco(tco_inputs, hourly_rate=100, horizon_years=3)
    
    assert result["horizon_cost"] is None
    assert result["annual_run_cost"] is None
    assert "Insufficient evidence-derived inputs" in result["explanation"]


def test_compute_tco_with_complete_inputs():
    """Test that compute_tco returns numeric outputs when inputs are complete."""
    tco_inputs = {
        "build_person_days": 10,
        "run_person_days_per_year": 5,
        "license_cost_per_year": 5000,
        "compute_cost_per_year": 2000,
        "training_hours": 40,
        "downtime_hours_per_year": 10
    }
    
    result = compute_tco(tco_inputs, hourly_rate=100, horizon_years=3)
    
    # Check that values are computed
    assert result["horizon_cost"] is not None
    assert result["annual_run_cost"] is not None
    assert result["horizon_cost"] > 0
    assert result["annual_run_cost"] > 0
    
    # Check breakdown exists
    assert "build_cost_once" in result["breakdown"]
    assert "training_cost_once" in result["breakdown"]
    assert "labor_run_cost_per_year" in result["breakdown"]
    
    # Verify calculations
    # Build: 10 days * 8 hours * $100 = $8,000
    assert result["breakdown"]["build_cost_once"] == 8000
    
    # Training: 40 hours * $100 = $4,000
    assert result["breakdown"]["training_cost_once"] == 4000
    
    # Annual run: (5 days * 8 hours * $100) + $5,000 + $2,000 + (10 hours * $100) = $4,000 + $5,000 + $2,000 + $1,000 = $12,000
    assert result["annual_run_cost"] == 12000
    
    # Horizon: $8,000 + $4,000 + 3 * $12,000 = $48,000
    assert result["horizon_cost"] == 48000


def test_compute_tco_all_missing():
    """Test TCO with all inputs missing."""
    tco_inputs = {
        "build_person_days": None,
        "run_person_days_per_year": None,
        "license_cost_per_year": None,
        "compute_cost_per_year": None,
        "training_hours": None,
        "downtime_hours_per_year": None
    }
    
    result = compute_tco(tco_inputs, hourly_rate=100, horizon_years=3)
    
    assert result["horizon_cost"] is None
    assert result["annual_run_cost"] is None
    assert result["breakdown"] == {}


def test_compute_productivity_with_missing_inputs():
    """Test that compute_productivity returns None outputs when both primary inputs are missing."""
    prod_inputs = {
        "time_saved_hours_per_month": None,
        "cost_avoided_per_year": None,
        "throughput_delta_per_year": None,
        "success_prob_delta": None
    }
    
    result = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
    
    assert result["horizon_productivity_value"] is None
    assert result["annual_productivity_value"] is None
    assert "Insufficient evidence-derived inputs" in result["explanation"]


def test_compute_productivity_with_time_saved_only():
    """Test productivity computation with only time_saved input."""
    prod_inputs = {
        "time_saved_hours_per_month": 10,
        "cost_avoided_per_year": None,
        "throughput_delta_per_year": None,
        "success_prob_delta": None
    }
    
    result = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
    
    # Should compute values
    assert result["horizon_productivity_value"] is not None
    assert result["annual_productivity_value"] is not None
    
    # Verify calculations
    # Annual hours: 10 * 12 = 120
    assert result["breakdown"]["annual_hours_saved"] == 120
    
    # Annual time value: 120 * $100 = $12,000
    assert result["breakdown"]["annual_time_value"] == 12000
    
    # Annual productivity: $12,000 + $0 = $12,000
    assert result["annual_productivity_value"] == 12000
    
    # Horizon: 3 * $12,000 = $36,000
    assert result["horizon_productivity_value"] == 36000


def test_compute_productivity_with_cost_avoided_only():
    """Test productivity computation with only cost_avoided input."""
    prod_inputs = {
        "time_saved_hours_per_month": None,
        "cost_avoided_per_year": 50000,
        "throughput_delta_per_year": None,
        "success_prob_delta": None
    }
    
    result = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
    
    # Should compute values
    assert result["horizon_productivity_value"] is not None
    assert result["annual_productivity_value"] is not None
    
    # Verify calculations
    assert result["breakdown"]["annual_hours_saved"] == 0
    assert result["breakdown"]["annual_time_value"] == 0
    assert result["breakdown"]["cost_avoided_per_year"] == 50000
    
    # Annual: $0 + $50,000 = $50,000
    assert result["annual_productivity_value"] == 50000
    
    # Horizon: 3 * $50,000 = $150,000
    assert result["horizon_productivity_value"] == 150000


def test_compute_productivity_with_both_inputs():
    """Test productivity computation with both time and cost inputs."""
    prod_inputs = {
        "time_saved_hours_per_month": 20,
        "cost_avoided_per_year": 30000,
        "throughput_delta_per_year": 5,
        "success_prob_delta": 0.1
    }
    
    result = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
    
    # Should compute values
    assert result["horizon_productivity_value"] is not None
    assert result["annual_productivity_value"] is not None
    
    # Verify calculations
    # Annual hours: 20 * 12 = 240
    assert result["breakdown"]["annual_hours_saved"] == 240
    
    # Annual time value: 240 * $100 = $24,000
    assert result["breakdown"]["annual_time_value"] == 24000
    
    # Annual: $24,000 + $30,000 = $54,000
    assert result["annual_productivity_value"] == 54000
    
    # Horizon: 3 * $54,000 = $162,000
    assert result["horizon_productivity_value"] == 162000
    
    # Directional values preserved
    assert result["throughput_delta_per_year"] == 5
    assert result["success_prob_delta"] == 0.1


def test_compute_tco_zero_horizon():
    """Test TCO with zero horizon (edge case)."""
    tco_inputs = {
        "build_person_days": 10,
        "run_person_days_per_year": 5,
        "license_cost_per_year": 5000,
        "compute_cost_per_year": 2000,
        "training_hours": 40,
        "downtime_hours_per_year": 10
    }
    
    result = compute_tco(tco_inputs, hourly_rate=100, horizon_years=0)
    
    # Should only have one-time costs
    assert result["horizon_cost"] == 8000 + 4000  # build + training
