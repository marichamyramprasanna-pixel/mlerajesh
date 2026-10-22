import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def generate():
    output_dir = Path(__file__).resolve().parent / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "Industrial_IoT_Predictive_Maintenance_250k.csv"
    
    if csv_path.exists():
        print(f"Dataset already exists at {csv_path}")
        return

    print("Generating Industrial IoT dataset with 250,000 rows...")
    rng = np.random.default_rng(42)
    n_rows = 250_000

    # Machines
    machines = [
        ("M-01", "Motor"),
        ("P-02", "Pump"),
        ("C-03", "Compressor"),
        ("F-04", "Fan")
    ]
    
    # Base allocations
    # ~80% Normal, ~20% Failures split among 5 failure types
    fault_classes = [
        "Normal",
        "Overheating",
        "Bearing Failure",
        "Motor Failure",
        "Power Failure",
        "Sensor Fault"
    ]
    # Class proportions: Normal 75%, other 5 classes 5% each
    fault_probs = [0.75, 0.05, 0.05, 0.05, 0.05, 0.05]
    
    chosen_faults = rng.choice(fault_classes, size=n_rows, p=fault_probs)
    failure_flags = np.where(chosen_faults == "Normal", 0, 1)

    # Machine assignment
    m_indices = rng.integers(0, len(machines), size=n_rows)
    m_ids = [machines[i][0] for i in m_indices]
    m_types = [machines[i][1] for i in m_indices]

    # Timestamp generation
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    # Generate sequential or uniform time steps
    seconds_offset = np.sort(rng.integers(0, 365 * 24 * 3600, size=n_rows))
    timestamps = [(start_time + timedelta(seconds=int(s))).strftime("%Y-%m-%d %H:%M:%S") for s in seconds_offset]

    # Generate multi-sensor features
    # Default baseline ranges
    vib = rng.normal(2.5, 0.6, size=n_rows)
    temp = rng.normal(45.0, 5.0, size=n_rows)
    curr = rng.normal(32.0, 4.5, size=n_rows)
    noise = rng.normal(55.0, 4.0, size=n_rows)
    rpm = rng.normal(1485.0, 15.0, size=n_rows)

    # Modulate features based on fault type
    # Overheating: High temp, elevated current & noise
    idx_over = (chosen_faults == "Overheating")
    temp[idx_over] = rng.uniform(78.0, 96.0, size=np.sum(idx_over))
    noise[idx_over] += rng.uniform(8.0, 15.0, size=np.sum(idx_over))
    curr[idx_over] += rng.uniform(15.0, 30.0, size=np.sum(idx_over))

    # Bearing Failure: High vibration, high acoustic noise
    idx_bearing = (chosen_faults == "Bearing Failure")
    vib[idx_bearing] = rng.uniform(9.0, 18.5, size=np.sum(idx_bearing))
    noise[idx_bearing] = rng.uniform(78.0, 97.0, size=np.sum(idx_bearing))
    temp[idx_bearing] += rng.uniform(10.0, 20.0, size=np.sum(idx_bearing))

    # Motor Failure: High current draw, speed drop, higher vibration
    idx_motor = (chosen_faults == "Motor Failure")
    curr[idx_motor] = rng.uniform(115.0, 185.0, size=np.sum(idx_motor))
    rpm[idx_motor] = rng.uniform(1050.0, 1350.0, size=np.sum(idx_motor))
    vib[idx_motor] += rng.uniform(3.5, 7.5, size=np.sum(idx_motor))
    temp[idx_motor] += rng.uniform(15.0, 28.0, size=np.sum(idx_motor))

    # Power Failure: Low current, low RPM
    idx_power = (chosen_faults == "Power Failure")
    curr[idx_power] = rng.uniform(0.5, 6.0, size=np.sum(idx_power))
    rpm[idx_power] = rng.uniform(500.0, 850.0, size=np.sum(idx_power))
    vib[idx_power] = rng.uniform(0.2, 1.2, size=np.sum(idx_power))
    noise[idx_power] = rng.uniform(40.0, 50.0, size=np.sum(idx_power))

    # Sensor Fault: Out-of-bounds, wild noise spikes or extreme pegs
    idx_sensor = (chosen_faults == "Sensor Fault")
    vib[idx_sensor] = rng.choice([0.0, 19.8, 15.0], size=np.sum(idx_sensor))
    noise[idx_sensor] = rng.choice([40.1, 99.5], size=np.sum(idx_sensor))
    temp[idx_sensor] = rng.choice([20.5, 99.8], size=np.sum(idx_sensor))

    # Clip to valid operational limits
    vib = np.clip(vib, 0.0, 20.0).round(2)
    temp = np.clip(temp, 20.0, 100.0).round(2)
    curr = np.clip(curr, 0.0, 200.0).round(2)
    noise = np.clip(noise, 40.0, 100.0).round(2)
    rpm = np.clip(rpm, 500.0, 5000.0).round(1)

    df = pd.DataFrame({
        "Machine_ID": m_ids,
        "Machine_Type": m_types,
        "Timestamp": timestamps,
        "Vibration_mm_s": vib,
        "Temperature_C": temp,
        "Current_A": curr,
        "Noise_dB": noise,
        "RPM": rpm,
        "Failure_Flag": failure_flags,
        "Failure_Type": chosen_faults,
    })

    print(f"Writing {len(df):,} rows to {csv_path}...")
    df.to_csv(csv_path, index=False)
    print("Dataset generated successfully!")

if __name__ == "__main__":
    generate()
