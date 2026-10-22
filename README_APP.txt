INDUSTRIAL FAULT DIAGNOSIS - UPDATED VERSION

Changes:
- Technical blue industrial UI.
- Multi-sensor values displayed as a pie chart.
- Removed Stage 2 and Stage 3 from the UI.
- Removed all line/normal signal graphs from the UI.
- DecisionTreeClassifier and RandomForestClassifier are the only ML algorithms.
- Model accuracy is calculated by the FastAPI backend and shown in the UI.
- Training data, test data and confusion matrices remain backend-only through /model/evaluation.
- No matplotlib dependency is required.
- Plotly is used for the sensor pie chart.
- Real supplied Industrial_IoT_Predictive_Maintenance_250k.csv data is used.
- Models use reproducible tuned training parameters; no synthetic labels are created.

Backend:
    uvicorn backend:app --host 127.0.0.1 --port 8520

App:
    streamlit run app.py
