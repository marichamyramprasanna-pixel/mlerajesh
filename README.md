# 🏭 Industrial IoT Machine Fault Diagnosis

An end-to-end intelligent Industrial IoT Predictive Maintenance and Fault Diagnosis platform using FastAPI, Streamlit, and Scikit-Learn.

## 🚀 Features

- **Multi-Sensor Telemetry Monitoring**: Real-time monitoring across 5 critical industrial sensor channels:
  - Vibration (`mm/s`)
  - Temperature (`°C`)
  - Current (`A`)
  - Acoustic Noise (`dB`)
  - Rotational Speed (`RPM`)
- **Machine Fleet Support**: Pre-configured profiles for:
  - `M-01` (Industrial Motor)
  - `P-02` (Industrial Pump)
  - `C-03` (Air Compressor)
  - `F-04` (Cooling Fan)
- **Machine Learning Diagnostics**:
  - **Decision Tree Classifier** & **Random Forest Classifier** trained on 250,000 industrial sensor telemetry records.
  - Automatic fault classification (`Normal`, `Overheating`, `Bearing Failure`, `Motor Failure`, `Power Failure`, `Sensor Fault`).
  - Dual-task architecture: separate binary health/failure detector + multiclass fault diagnostic model.
- **Modern Industrial Dashboard**:
  - Technical blue industrial UI theme.
  - Multi-sensor distribution visualization using Plotly donut chart with normalized relative intensity.
  - Real-time diagnostic metrics, confidence scores, and health percentage indicators.
  - Specific prescriptive maintenance recommendations based on detected failure modes.
- **FastAPI Microservice Backend**:
  - Model training, evaluation, and confusion matrices retained in the backend.
  - RESTful endpoints for health status, dataset statistics, sensor streams, and diagnosis.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit, Plotly
- **Machine Learning**: Scikit-Learn, NumPy, Pandas

---

## 📦 Quick Start

### 1. Prerequisites
- Python 3.10+ (or Python 3.11/3.12 via `uv`)

### 2. Installation

Clone the repository and install the dependencies:
```bash
git clone https://github.com/marichamyramprasanna-pixel/mlerajesh.git
cd mlerajesh

# Create virtual environment and install requirements
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` to set up environment credentials:
```bash
cp .env.example .env
```

### 4. Generate Dataset (if not already present)
```bash
python generate_dataset.py
```

### 5. Running the Application

You can start both services automatically on Windows using:
```cmd
Launch_Machine_Fault_Diagnosis_App.bat
```

Or start the services manually:

**Terminal 1 - FastAPI Backend:**
```bash
uvicorn backend:app --host 127.0.0.1 --port 8520
```

**Terminal 2 - Streamlit Frontend:**
```bash
streamlit run app.py --server.port 8512
```

Open your browser at **`http://localhost:8512`**.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Backend status, active data source, and row count |
| `GET` | `/dataset/info` | Class counts and features list |
| `GET` | `/dataset/sample` | Sample records from the dataset |
| `POST` | `/start/{machine}` | Initialize stream for a specific machine |
| `POST` | `/read/{machine}` | Fetch latest telemetry readings |
| `POST` | `/diagnose` | Run ML diagnosis on 5-channel sensor input |
| `GET` | `/model/accuracy` | Model accuracy and performance metrics |
| `GET` | `/model/evaluation` | Full evaluation metrics, confusion matrix (backend-only) |
| `GET` | `/history/{machine}` | Historical sensor samples |
