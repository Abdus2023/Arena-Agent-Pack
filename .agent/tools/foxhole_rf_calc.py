#!/usr/bin/env python3
"""Small deterministic RF calculator for FOXHOLE LAB.

Calculations are idealized. They do not model detector nonlinearity, matching,
parasitics, antenna efficiency, or measured device performance.
"""
from __future__ import annotations
import argparse
import json
import math

K_B = 1.380649e-23

def positive(name: str, value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and > 0")
    return value

def finite_result(name: str, value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} is outside the representable numeric range")
    return value

def resonant_capacitance(frequency_hz: float, inductance_h: float) -> float:
    f = positive("frequency_hz", frequency_hz)
    l = positive("inductance_h", inductance_h)
    try:
        result = 1.0 / ((2.0 * math.pi * f) ** 2 * l)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("resonant capacitance is outside the representable numeric range") from exc
    return positive("calculated_capacitance_f", finite_result("calculated_capacitance_f", result))

def resonant_frequency(inductance_h: float, capacitance_f: float) -> float:
    l = positive("inductance_h", inductance_h)
    c = positive("capacitance_f", capacitance_f)
    try:
        result = 1.0 / (2.0 * math.pi * math.sqrt(l * c))
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("resonant frequency is outside the representable numeric range") from exc
    return positive("calculated_frequency_hz", finite_result("calculated_frequency_hz", result))

def bandwidth_hz(center_hz: float, q: float) -> float:
    result = positive("center_hz", center_hz) / positive("q", q)
    return positive("calculated_bandwidth_hz", finite_result("calculated_bandwidth_hz", result))

def thermal_noise_rms(resistance_ohm: float, bandwidth_hz_value: float, temperature_k: float = 290.0) -> float:
    r = positive("resistance_ohm", resistance_ohm)
    b = positive("bandwidth_hz", bandwidth_hz_value)
    t = positive("temperature_k", temperature_k)
    try:
        result = math.sqrt(4.0 * K_B * t * r * b)
    except (OverflowError, ValueError) as exc:
        raise ValueError("thermal-noise result is outside the representable numeric range") from exc
    return finite_result("noise_rms_v", result)

def dbm_to_watts(dbm: float) -> float:
    if not math.isfinite(dbm):
        raise ValueError("dbm must be finite")
    try:
        result = 1e-3 * (10.0 ** (dbm / 10.0))
    except OverflowError as exc:
        raise ValueError("power is outside the representable numeric range") from exc
    return finite_result("power_w", result)

def rectification_ratio(forward_current_a: float, reverse_current_a: float) -> float:
    f = positive("forward_current_a", abs(forward_current_a))
    r = positive("reverse_current_a", abs(reverse_current_a))
    return finite_result("rectification_ratio", f / r)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("capacitance")
    p.add_argument("--frequency-hz", type=float, required=True)
    p.add_argument("--inductance-h", type=float, required=True)
    p = sub.add_parser("frequency")
    p.add_argument("--inductance-h", type=float, required=True)
    p.add_argument("--capacitance-f", type=float, required=True)
    p = sub.add_parser("bandwidth")
    p.add_argument("--center-hz", type=float, required=True)
    p.add_argument("--q", type=float, required=True)
    p = sub.add_parser("thermal-noise")
    p.add_argument("--resistance-ohm", type=float, required=True)
    p.add_argument("--bandwidth-hz", type=float, required=True)
    p.add_argument("--temperature-k", type=float, default=290.0)
    p = sub.add_parser("dbm-to-watts")
    p.add_argument("--dbm", type=float, required=True)
    p = sub.add_parser("rectification-ratio")
    p.add_argument("--forward-current-a", type=float, required=True)
    p.add_argument("--reverse-current-a", type=float, required=True)
    args = parser.parse_args()
    try:
        if args.operation == "capacitance":
            result = {"capacitance_f": resonant_capacitance(args.frequency_hz, args.inductance_h)}
        elif args.operation == "frequency":
            result = {"frequency_hz": resonant_frequency(args.inductance_h, args.capacitance_f)}
        elif args.operation == "bandwidth":
            result = {"bandwidth_hz": bandwidth_hz(args.center_hz, args.q)}
        elif args.operation == "thermal-noise":
            result = {"noise_rms_v": thermal_noise_rms(args.resistance_ohm, args.bandwidth_hz, args.temperature_k)}
        elif args.operation == "dbm-to-watts":
            result = {"power_w": dbm_to_watts(args.dbm)}
        else:
            result = {"rectification_ratio": rectification_ratio(args.forward_current_a, args.reverse_current_a)}
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
