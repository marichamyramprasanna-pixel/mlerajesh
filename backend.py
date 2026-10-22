from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

app = FastAPI(title="Industrial Fault Diagnosis Backend", version="3.0")

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "datasets" / "Industrial_IoT_Predictive_Maintenance_250k.csv"

# Five multi-sensor channels used by the application.
FEATURES = ["Vibration_mm_s", "Temperature_C", "Current_A", "Noise_dB", "RPM"]
UNITS = ["mm/s", "°C", "A", "dB", "RPM"]
TARGET = "Failure_Type"
FAILURE_TARGET = "Failure_Flag"

MACHINE_FILTERS = {
    "M-01": None,
    "P-02": "Pump",
    "C-03": "Compressor",
    "F-04": None,
}

MACHINES = {
    "M-01": {"name": "Industrial Motor M-01", "type": "Motor"},
    "P-02": {"name": "Industrial Pump P-02", "type": "Pump"},
    "C-03": {"name": "Air Compressor C-03", "type": "Compressor"},
    "F-04": {"name": "Cooling Fan F-04", "type": "Fan"},
}

DATA = None
MODELS = None
MODEL_CLASSES = None
FAILURE_MODELS = None
EVALUATION = None
active = {}
run_counts = {k: 0 for k in MACHINES}


def load_dataset():
    global DATA
    if DATA is None:
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
        DATA = pd.read_csv(DATASET_PATH)

        required = FEATURES + [TARGET, FAILURE_TARGET]
        missing = [c for c in required if c not in DATA.columns]
        if missing:
            raise ValueError(f"Dataset is missing required columns: {missing}")

        DATA[TARGET] = DATA[TARGET].fillna("Normal").astype(str)
        DATA[FAILURE_TARGET] = pd.to_numeric(
            DATA[FAILURE_TARGET], errors="coerce"
        ).fillna(0).astype(int)

        for col in FEATURES:
            DATA[col] = pd.to_numeric(DATA[col], errors="coerce")

        DATA = DATA.dropna(subset=FEATURES).reset_index(drop=True)
    return DATA


def balanced_training_sample(data, per_class=6000):
    """Use a reproducible balanced sample so model training stays practical."""
    rng = np.random.default_rng(42)
    parts = []
    for label, group in data.groupby(TARGET):
        n = min(per_class, len(group))
        parts.append(
            group.sample(
                n=n,
                random_state=int(rng.integers(0, 1_000_000))
            )
        )
    return pd.concat(parts, ignore_index=True)


def build_fault_models():
    """
    Tuned Decision Tree + Random Forest.
    Both are trained on the real supplied dataset; no synthetic sensor values
    or artificial labels are generated.
    """
    data = balanced_training_sample(load_dataset(), per_class=6000)
    X = data[FEATURES].astype(float)
    y = data[TARGET].astype(str)

    models = [
        DecisionTreeClassifier(
            criterion="entropy",
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=120,
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    for model in models:
        model.fit(X, y)

    return models


def get_models():
    global MODELS, MODEL_CLASSES
    if MODELS is None:
        MODELS = build_fault_models()
        MODEL_CLASSES = MODELS[0].classes_
    return MODELS


def balanced_failure_sample(data, per_class=6000):
    """Balanced Normal/Failure sample for the separate health detector."""
    normal = data[data[FAILURE_TARGET] == 0]
    failure = data[data[FAILURE_TARGET] == 1]
    n = min(per_class, len(normal), len(failure))
    return pd.concat([
        normal.sample(n=n, random_state=42),
        failure.sample(n=n, random_state=43),
    ], ignore_index=True)


def build_failure_models():
    """Models for the separate Normal/Failure detection task."""
    data = balanced_failure_sample(load_dataset(), per_class=6000)
    X = data[FEATURES].astype(float)
    y = data[FAILURE_TARGET].astype(int)

    models = [
        DecisionTreeClassifier(
            criterion="gini",
            max_depth=14,
            min_samples_split=4,
            min_samples_leaf=3,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=120,
            max_depth=18,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    for model in models:
        model.fit(X, y)
    return models


def get_failure_models():
    global FAILURE_MODELS
    if FAILURE_MODELS is None:
        FAILURE_MODELS = build_failure_models()
    return FAILURE_MODELS


def evaluate_models():
    """
    Backend-only evaluation:
    - 80% training data
    - 20% held-out test data
    - confusion matrices remain available through this endpoint only
    """
    global EVALUATION
    if EVALUATION is not None:
        return EVALUATION

    data = balanced_training_sample(load_dataset(), per_class=6000)
    X = data[FEATURES].astype(float)
    y = data[TARGET].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    fault_models = [
        DecisionTreeClassifier(
            criterion="entropy",
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=120,
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    labels = [str(x) for x in sorted(y.unique())]
    results = []
    matrices = {}

    for model in fault_models:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        name = model.__class__.__name__

        results.append({
            "model": name,
            "accuracy": round(accuracy_score(y_test, pred) * 100, 2),
            "precision": round(
                precision_score(
                    y_test, pred, average="weighted", zero_division=0
                ) * 100, 2
            ),
            "recall": round(
                recall_score(
                    y_test, pred, average="weighted", zero_division=0
                ) * 100, 2
            ),
            "f1": round(
                f1_score(
                    y_test, pred, average="weighted", zero_division=0
                ) * 100, 2
            ),
        })
        matrices[name] = confusion_matrix(
            y_test, pred, labels=labels
        ).tolist()

    # Separate binary health/failure detection accuracy.
    binary_data = balanced_failure_sample(load_dataset(), per_class=6000)
    Xb = binary_data[FEATURES].astype(float)
    y_binary = binary_data[FAILURE_TARGET].astype(int)
    Xb_train, Xb_test, yb_train, yb_test = train_test_split(
        Xb, y_binary, test_size=0.20, random_state=42, stratify=y_binary
    )
    binary_results = []

    binary_models = [
        DecisionTreeClassifier(
            criterion="gini",
            max_depth=14,
            min_samples_split=4,
            min_samples_leaf=3,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=120,
            max_depth=18,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    for model in binary_models:
        model.fit(Xb_train, yb_train)
        pred = model.predict(Xb_test)
        binary_results.append({
            "model": model.__class__.__name__,
            "accuracy": round(accuracy_score(yb_test, pred) * 100, 2),
            "precision": round(
                precision_score(yb_test, pred, zero_division=0) * 100, 2
            ),
            "recall": round(
                recall_score(yb_test, pred, zero_division=0) * 100, 2
            ),
            "f1": round(
                f1_score(yb_test, pred, zero_division=0) * 100, 2
            ),
        })

    EVALUATION = {
        "dataset_rows": int(len(load_dataset())),
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "classes": labels,
        "fault_type_models": results,
        "failure_detection_models": binary_results,
        # Backend-only data. The Streamlit interface intentionally does not display it.
        "confusion_matrices": matrices,
        "test_data_sample": pd.DataFrame({
            **{c: X_test[c].reset_index(drop=True) for c in FEATURES},
            "Actual_Failure_Type": y_test.reset_index(drop=True),
            "Predicted_Failure_Type": fault_models[1].predict(X_test),
        }).head(100).to_dict(orient="records"),
    }
    return EVALUATION


def dataset_rows_for_machine(machine: str):
    data = load_dataset()
    machine_type = MACHINE_FILTERS.get(machine)
    if machine_type and "Machine_Type" in data.columns:
        subset = data[data["Machine_Type"].eq(machine_type)]
        if len(subset):
            return subset
    return data


def row_to_values(row):
    return [
        round(float(row["Vibration_mm_s"]), 2),
        round(float(row["Temperature_C"]), 2),
        round(float(row["Current_A"]), 2),
        round(float(row["Noise_dB"]), 2),
        round(float(row["RPM"]), 1),
    ]


def diagnosis_for_values(machine, values):
    models = get_models()
    failure_models = get_failure_models()
    x = np.asarray(values, dtype=float).reshape(1, -1)

    predictions = [m.predict(x)[0] for m in models]
    probability_arrays = [m.predict_proba(x)[0] for m in models]

    classes = models[0].classes_
    mean_prob = np.mean(probability_arrays, axis=0)
    order = np.argsort(mean_prob)[::-1]

    fault = str(classes[order[0]])
    confidence = float(mean_prob[order[0]] * 100)

    # Binary failure detection is more reliable for the Normal/Failure decision.
    failure_predictions = [int(m.predict(x)[0]) for m in failure_models]
    failure_probability = float(
        np.mean([m.predict_proba(x)[0][1] for m in failure_models]) * 100
    )
    is_failure = failure_probability >= 50

    if not is_failure:
        status = "Healthy"
        fault = "Normal"
        health = max(75, min(99, int(100 - failure_probability * 0.35)))
    else:
        status = "Critical" if failure_probability >= 75 else "Warning"
        health = max(20, min(74, int(100 - failure_probability)))

    details = []
    for model, prediction, probs in zip(models, predictions, probability_arrays):
        idx = int(np.where(model.classes_ == prediction)[0][0])
        details.append({
            "model": model.__class__.__name__,
            "prediction": str(prediction),
            "confidence": round(float(probs[idx] * 100), 1),
        })

    agreement = (
        sum(p == predictions[0] for p in predictions) / len(predictions) * 100
    )

    return {
        "machine": machine,
        "fault": fault,
        "status": status,
        "health": health,
        "confidence": round(confidence, 1),
        "failure_probability": round(failure_probability, 1),
        "failure_model_agreement": round(
            sum(p == failure_predictions[0] for p in failure_predictions)
            / len(failure_predictions) * 100,
            1,
        ),
        "agreement": round(agreement, 1),
        "models": details,
    }


class Reading(BaseModel):
    machine: str
    values: list[float]


@app.get("/health")
def health():
    data = load_dataset()
    return {
        "status": "ok",
        "service": "fault-diagnosis-backend",
        "data_source": DATASET_PATH.name,
        "rows": int(len(data)),
        "algorithms": ["DecisionTreeClassifier", "RandomForestClassifier"],
        "mode": "dataset-backed",
    }


@app.get("/machines")
def machines():
    return MACHINES


@app.get("/dataset/info")
def dataset_info():
    data = load_dataset()
    counts = data[TARGET].value_counts(dropna=False).to_dict()
    return {
        "file": DATASET_PATH.name,
        "rows": int(len(data)),
        "columns": list(data.columns),
        "features_used_for_diagnosis": FEATURES,
        "target": TARGET,
        "class_counts": {str(k): int(v) for k, v in counts.items()},
    }


@app.get("/dataset/sample")
def dataset_sample(n: int = 10):
    data = load_dataset()
    n = max(1, min(int(n), 100))
    sample = data.sample(n=n, random_state=42)
    cols = ["Machine_ID", "Machine_Type", "Timestamp"] + FEATURES + [
        "Failure_Flag", TARGET
    ]
    cols = [c for c in cols if c in sample.columns]
    return sample[cols].to_dict(orient="records")


@app.post("/start/{machine}")
def start(machine: str):
    if machine not in MACHINES:
        raise HTTPException(404, "Unknown machine")

    rows = dataset_rows_for_machine(machine)
    run_counts[machine] += 1
    row_index = (run_counts[machine] - 1) % len(rows)
    row = rows.iloc[row_index]
    active[machine] = row

    return {
        "machine": machine,
        "fault_profile": str(row[TARGET]),
        "run_number": run_counts[machine],
        "data_source": "supplied_dataset",
        "dataset_machine_id": str(row.get("Machine_ID", "")),
    }


@app.post("/read/{machine}")
def read(machine: str):
    if machine not in MACHINES:
        raise HTTPException(404, "Unknown machine")

    rows = dataset_rows_for_machine(machine)

    if machine in active:
        row = active[machine]
    else:
        idx = run_counts[machine] % len(rows)
        row = rows.iloc[idx]
        active[machine] = row

    values = row_to_values(row)

    return {
        "machine": machine,
        "values": values,
        "units": UNITS,
        "timestamp": str(row.get("Timestamp", "")),
        "data_source": DATASET_PATH.name,
        "dataset_machine_id": str(row.get("Machine_ID", "")),
        "machine_type": str(row.get("Machine_Type", "")),
        "ground_truth": str(row[TARGET]),
        "failure_flag": int(row.get(FAILURE_TARGET, 0)),
    }


@app.post("/diagnose")
def diagnosis(req: Reading):
    if req.machine not in MACHINES:
        raise HTTPException(404, "Unknown machine")
    if len(req.values) != len(FEATURES):
        raise HTTPException(400, f"Exactly {len(FEATURES)} sensor values required")

    result = diagnosis_for_values(req.machine, req.values)

    row = active.get(req.machine)
    if row is not None:
        result["ground_truth"] = str(row[TARGET])
        result["dataset_machine_id"] = str(row.get("Machine_ID", ""))
        result["data_source"] = "supplied_dataset"

    return result


@app.get("/model/accuracy")
def model_accuracy():
    """Compact backend endpoint containing the requested accuracy data."""
    ev = evaluate_models()
    return {
        "algorithms": ev["fault_type_models"],
        "failure_detection_accuracy": ev["failure_detection_models"],
    }


@app.get("/model/evaluation")
def model_evaluation():
    """Full backend evaluation. Train/test rows and confusion matrices stay backend-only."""
    return evaluate_models()


@app.get("/history/{machine}")
def history(machine: str, samples: int = 30):
    if machine not in MACHINES:
        raise HTTPException(404, "Unknown machine")

    samples = max(10, min(int(samples), 120))
    rows = dataset_rows_for_machine(machine)
    start = max(0, (run_counts[machine] * samples) % max(1, len(rows) - samples))
    selected = rows.iloc[start:start + samples]

    if len(selected) < samples:
        selected = pd.concat(
            [selected, rows.iloc[:samples - len(selected)]],
            ignore_index=True
        )

    return {
        "machine": machine,
        "samples": [row_to_values(r) for _, r in selected.iterrows()],
        "units": UNITS,
        "data_source": DATASET_PATH.name,
    }
