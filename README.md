# 🧬 DiabetesTwin-AI

**Personalized Diabetes Monitoring Twin** — a predictive digital twin connected to a virtual-patient environment for interactive glucose monitoring and lifestyle what-if simulation.

> **Important:** this repository is a student research/education prototype. It uses synthetic virtual-patient data by default and is **not medical advice, a diagnosis tool, a CGM, or a medical device**. It does not recommend medication or insulin doses.

## Team

- Regis LIKASSI
- Hakim DJOMO
- Jean Direl NZE
- Xavier ONDO
- Seth NDINGA

## What is already implemented

- 🧍 Personalized virtual-patient profiles (`balanced`, `insulin_resistant`, `active`)
- 🍽️ Meal/carbohydrate effects
- 🏃 Physical-activity effects
- 😴 Sleep and stress effects
- 📈 24-hour CGM-like trajectory at 5-minute resolution
- 🎯 ADA-style TIR/TBR/TAR reporting metrics
- 🧪 Interactive lifestyle **what-if** comparison
- 🤖 30-minute-ahead ML prediction demo with `HistGradientBoostingRegressor`
- 🔗 FHIR R5-compatible synthetic glucose export
- 🖥️ Streamlit dashboard
- ⚡ FastAPI endpoints
- 🐳 Docker Compose
- ✅ Unit/API tests and GitHub Actions CI
- 📚 Architecture, model card and research plan

## Architecture

```text
Patient profile + lifestyle events
              |
              v
   Physiology-inspired twin
       |               |
       |               +--> synthetic longitudinal data --> ML predictor
       v
CGM-like trajectory
       |
       +--> Streamlit dashboard / what-if simulation
       +--> ADA-style metrics
       +--> FHIR Observation export
       +--> FastAPI
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for details.

## Quick start

### 1) Python

```bash
git clone https://github.com/jeandirel/DiabetesTwin-AI.git
cd DiabetesTwin-AI
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
streamlit run app.py
```

Dashboard: `http://localhost:8501`

### 2) API

```bash
uvicorn api:app --reload
```

OpenAPI docs: `http://localhost:8000/docs`

### 3) Docker

```bash
docker compose up --build
```

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000/docs`

## Example API request

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "name": "Twin-01",
      "age": 45,
      "phenotype": "balanced",
      "baseline_glucose": 112,
      "carb_sensitivity": 0.72,
      "activity_sensitivity": 18,
      "stress_sensitivity": 16,
      "circadian_amplitude": 7
    },
    "scenario": {
      "meals": [
        {"hour": 8, "carbs_g": 45, "label": "Breakfast"},
        {"hour": 13, "carbs_g": 65, "label": "Lunch"}
      ],
      "exercise": [
        {"hour": 18, "duration_min": 35, "intensity": 0.55, "label": "Walk"}
      ],
      "stress": 0.25,
      "sleep_hours": 7.5,
      "sleep_quality": 0.8
    },
    "seed": 42,
    "step_minutes": 5
  }'
```

## Train the synthetic prediction layer

```bash
python scripts/train_model.py --phenotype balanced --days 42
```

The script writes a local `artifacts/predictor.joblib` file (ignored by Git).

## Tests and quality

```bash
pytest -q
ruff check .
```

## Scientific basis

The implementation is deliberately conservative about clinical claims:

- The **70–180 mg/dL** CGM time-in-range reporting band comes from the ADA 2026 Standards of Care for most adults; individual targets can differ.
- The project is inspired by the established concept of in-silico virtual patients such as the UVA/Padova T1D simulator, but this code is **not** UVA/Padova and is not clinically validated.
- For a future real-data phase, PhysioNet **CGMacros** provides CGM + macronutrient + activity data from healthy, prediabetes and type 2 diabetes participants.
- The interoperability demonstration uses HL7 FHIR `Observation` resources.

See [`docs/RESEARCH.md`](docs/RESEARCH.md) and [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

## Suggested project roadmap

- [x] MVP digital-twin simulator
- [x] interactive dashboard
- [x] what-if lifestyle scenarios
- [x] synthetic ML prediction layer
- [x] FHIR export + REST API
- [x] automated tests / CI
- [ ] CGMacros ingestion pipeline
- [ ] patient-level real-data baselines
- [ ] uncertainty calibration
- [ ] external validation / subgroup analysis
- [ ] human-in-the-loop research protocol

## License

MIT — see [`LICENSE`](LICENSE).
