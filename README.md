# 🧬 DiabetesTwin-AI

**Personalized Diabetes Monitoring Twin** — a predictive digital twin connected to a virtual-patient environment for interactive glucose monitoring, real-data forecasting, and lifestyle what-if simulation.

> **Important:** this repository is a student research/education prototype. It is **not medical advice, a diagnosis tool, a CGM, or a medical device**. It does not recommend medication or insulin doses.

## Team

- Regis LIKASSI
- Hakim DJOMO
- Jean Direl NZE
- Xavier ONDO
- Seth NDINGA

## What is implemented

- 🧍 Personalized synthetic virtual-patient profiles (`balanced`, `insulin_resistant`, `active`)
- 🍽️ Meal/carbohydrate effects
- 🏃 Physical-activity effects
- 😴 Sleep and stress effects
- 📈 24-hour CGM-like synthetic trajectory at 5-minute resolution
- 🎯 TIR/TBR/TAR glucose reporting metrics
- 🧪 Interactive lifestyle **what-if** comparison
- 🤖 Synthetic 30-minute-ahead forecasting baseline
- 🌍 **Real PhysioNet CGMacros ingestion and preprocessing pipeline**
- 🩸 Dexcom G6 or Libre glucose parsing with meal, Fitbit, demographic and laboratory context
- 👤 Participant-specific chronological forecasting evaluation
- 👥 Participant-level holdout evaluation to reduce person leakage
- 🌲 HistGradientBoosting and Random Forest real-data baselines
- 📊 Real CGM vs predicted +30-minute glucose visualization in Streamlit
- 🔗 FHIR R5-compatible synthetic glucose export
- ⚡ FastAPI endpoints
- 🐳 Docker Compose
- ✅ Unit/API/real-data pipeline tests and GitHub Actions CI
- 📚 Architecture, model card, research plan and third-party data notice

## Architecture

```text
                         +-----------------------------+
                         | PhysioNet CGMacros v1.0.0  |
                         | CGM + meals + Fitbit + bio |
                         +-------------+---------------+
                                       |
                                       v
                             real-data preprocessing
                                       |
                       +---------------+----------------+
                       |                                |
                       v                                v
             participant holdout ML          personalized temporal ML
                       |                                |
                       +---------------+----------------+
                                       |
                                       v
                              observed vs predicted

Patient profile + lifestyle events
              |
              v
   physiology-inspired simulator
              |
              +--> synthetic longitudinal data --> synthetic ML baseline
              |
              +--> what-if scenarios / metrics / FHIR / API
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the detailed design.

## Quick start

```bash
git clone https://github.com/jeandirel/DiabetesTwin-AI.git
cd DiabetesTwin-AI
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install and launch:

```bash
pip install -e ".[dev]"
streamlit run app.py
```

Dashboard: `http://localhost:8501`

## Real CGMacros data

The repository **does not redistribute the raw dataset**. The official CGMacros archive is about 627 MB and is licensed separately under **CC BY-NC-SA 4.0**.

Source:

- Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*, PhysioNet v1.0.0, 2025.
- DOI: `10.13026/3z8q-x658`
- Official page: `https://physionet.org/content/cgmacros/1.0.0/`

CGMacros contains data from 45 participants: 15 healthy, 16 with prediabetes, and 14 with type 2 diabetes. It includes Dexcom G6 Pro and Abbott FreeStyle Libre Pro CGM data, Fitbit activity/heart rate, meal macronutrients, demographics, anthropometrics and laboratory variables.

### 1. Download the official dataset

```bash
python scripts/download_cgmacros.py
```

The downloader:

1. downloads directly from PhysioNet;
2. verifies the official SHA-256 checksum;
3. extracts to `data/raw/cgmacros/`;
4. keeps the third-party dataset outside Git tracking.

### 2. Build the forecasting table

```bash
python scripts/preprocess_cgmacros.py
```

Default output:

```text
data/processed/cgmacros_forecasting.csv.gz
```

The pipeline creates 30-minute forecasting samples with features including:

- current glucose;
- glucose lags at 15 and 30 minutes;
- recent glucose slope;
- time-of-day cyclical features;
- carbohydrates/protein/fat/fiber in the previous 120 minutes;
- rolling heart rate, METs and activity calories;
- age, BMI, HbA1c, fasting glucose and fasting insulin.

Dexcom is used by default because the study sampled it more frequently than Libre. To use Libre:

```bash
python scripts/preprocess_cgmacros.py --glucose-source libre
```

### 3. Compare real-data models

Strict participant-level holdout:

```bash
python scripts/train_real_model.py --compare
```

This keeps entire participants in either train or test, rather than randomly mixing adjacent measurements from the same person.

Train one grouped model:

```bash
python scripts/train_real_model.py --model hgb --split grouped
```

Train a personalized model for one participant using an earlier-70% / later-30% chronological split:

```bash
python scripts/train_real_model.py --model hgb --split personalized --participant 001
```

The evaluation reports MAE, RMSE and a persistence baseline. Model artifacts and prediction CSV files are written locally to `artifacts/` and ignored by Git.

### 4. Explore a real patient in the dashboard

After preprocessing:

```bash
streamlit run app.py
```

Open the **🌍 Real CGMacros** tab, choose a participant, inspect the released CGM trajectory, and train the participant-specific +30-minute model interactively.

> CGMacros dates are privacy-shifted by the dataset authors. The project does not attempt to reverse that transformation.

## Synthetic digital twin mode

The project also keeps a physiology-inspired educational simulator so that lifestyle scenarios can be changed interactively without pretending to alter a real patient record.

Train the synthetic prediction baseline:

```bash
python scripts/train_model.py --phenotype balanced --days 42
```

## API

```bash
uvicorn api:app --reload
```

OpenAPI docs: `http://localhost:8000/docs`

Example simulation request:

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

## Docker

```bash
docker compose up --build
```

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000/docs`

Raw CGMacros data are not copied into the Docker image. Mount the local `data/` directory if you want the real-data tab inside a container.

## Tests and quality

```bash
pytest -q
ruff check .
```

The CI tests use small generated fixtures that reproduce the CGMacros schema. The 627 MB third-party dataset is not downloaded during CI.

## Scientific scope

The project deliberately separates three claims:

1. **Synthetic simulator:** useful for software demonstration and what-if interaction, but not clinically validated physiology.
2. **Real-data forecasting:** trained/evaluated on the public CGMacros research dataset, but still not a clinical model.
3. **Digital twin research direction:** a future validated system would require prospective evaluation, calibration, external cohorts, uncertainty estimation, subgroup analysis and clinical governance.

The project is inspired by established in-silico diabetes simulation work, but it is not the UVA/Padova simulator and makes no regulatory claim.

See [`docs/RESEARCH.md`](docs/RESEARCH.md), [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md), and [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md).

## Roadmap

- [x] MVP virtual-patient simulator
- [x] interactive dashboard
- [x] lifestyle what-if scenarios
- [x] synthetic ML baseline
- [x] FHIR export + REST API
- [x] automated tests / CI
- [x] official CGMacros downloader with checksum verification
- [x] real CGMacros preprocessing
- [x] participant-level real-data baseline
- [x] personalized chronological baseline
- [x] real patient visualization in Streamlit
- [ ] calibrated predictive uncertainty
- [ ] external dataset validation
- [ ] subgroup/fairness analysis with adequate sample sizes
- [ ] prospective human-in-the-loop study protocol
- [ ] regulated medical-device pathway, only if the project ever moves beyond research

## Licensing

Repository source code: **MIT** — see [`LICENSE`](LICENSE).

CGMacros data: **CC BY-NC-SA 4.0**, owned/licensed by its original authors and distributed by PhysioNet. The raw dataset is not included in this repository. See [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md).
