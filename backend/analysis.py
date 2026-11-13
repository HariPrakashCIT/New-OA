"""Descriptive rule-based analysis only; thresholds are engineering heuristics."""
import numpy as np
import pandas as pd

def analyze(rows):
    disclaimer = 'Uncalibrated ADC signals; not a diagnosis, knee-force measurement or validated gait assessment.'
    if not rows:
        return dict(samples=0, status='No data', shares=None, observations=['Connect your insole and collect readings to begin.'], recommendations=['Check sensor placement and calibrate each FSR before interpreting distribution.'], disclaimer=disclaimer)
    frame = pd.DataFrame(rows)
    values = frame[['heel_pressure','ball_pressure','toe_pressure']].to_numpy(dtype=float)
    totals = values.sum(axis=1)
    loaded = values[totals > 150]
    shares = None if not len(loaded) else (loaded.sum(axis=0)/loaded.sum()*100).round(1).tolist()
    observations = [f'{len(values)} valid samples received; {len(loaded)} above the contact heuristic.']
    recommendations = ['Use the same footwear and sensor placement when comparing sessions.']
    if shares is None:
        observations.append('Insufficient contact signal for relative distribution.')
        recommendations.append('Check insole placement, wiring and sensor calibration.')
    else:
        dominant = int(np.argmax(shares))
        observations.append(f"{'Heel Ball Toe'.split()[dominant]} has the largest relative ADC signal ({shares[dominant]}%).")
        if max(shares) > 70:
            observations.append('One sensor contributes over 70% of loaded signal; this may reflect placement or calibration.')
            recommendations.append('Inspect sensor placement and repeat calibration before drawing conclusions.')
    times = pd.to_datetime(frame.timestamp, utc=True).sort_values()
    if len(times)>1 and times.diff().dt.total_seconds().max() > 5:
        observations.append('Recording gaps exceed 5 seconds; session coverage is incomplete.')
    if (values >= 4090).any():
        observations.append('At least one sensor is near ADC saturation.')
        recommendations.append('Check voltage divider sizing and calibration for saturated sensors.')
    return dict(samples=len(values), status='Descriptive analysis', shares=shares, observations=observations, recommendations=recommendations, disclaimer=disclaimer)
