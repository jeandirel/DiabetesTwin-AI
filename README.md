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
- 🧳 **Bundled licensed CGMacros demo subset for instant deployments**
- 🩸 Dexcom or Libre glucose parsing with meal, Fitbit, demographic and laboratory context
- 👤 Participant-specific chronological forecasting evaluation
- 👥 Participant-level holdout evaluation to reduce person leakage
- 🌲 HistGradientBoosting and Random Forest real-data baselines
- 📊 Real CGM vs predicted +30-minute glucose visualization in Streamlit
- 🔗 FHIR R5-compatible synthetic glucose export
- ⚡ FastAPI endpoints
- 🐳 Docker Compose
- ✅ Unit/API/real-data pipeline tests and GitHub Actions CI
- 📚 Architecture, model card, research plan, benchmark report and third-party data notice

## Verified real-data benchmark

The full official CGMacros v1.0.0 archive has been downloaded, checksum-verified, preprocessed and benchmarked end to end with GitHub Actions.

- **45 / 45 participants** processed
- **621,069** usable +30-minute forecasting rows
- grouped split: **36 train participants / 9 unseen test participants**
- Random Forest grouped MAE: **13.11 mg/dL**
- HistGradientBoosting grouped MAE: **13.40 mg/dL**
- grouped persistence MAE: **13.39 mg/dL**
- personalized HGB median MAE across 45 participants: **12.05 mg/dL**
- personalized HGB beats persistence for **20 / 45** participants and ties for 1

The current personalized baseline therefore **does not consistently outperform persistence**. That limitation is reported explicitly rather than hidden.

See [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md) for methodology, metrics and interpretation.

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

The **🌍 Real CGMacros** tab works immediately with the small licensed demo subset committed in `data/demo/`. If the full preprocessed dataset is present locally, the dashboard automatically prefers it over the demo subset.

## Real CGMacros data

The repository **does not redistribute the full raw dataset**. The official CGMacros archive is about 627 MB and is licensed separately under **CC BY-NC-SA 4.0**. A small derived deployment subset is included under that same data license so hosted demos can show real CGM forecasting without downloading 627 MB at startup.

Source:

- Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*, PhysioNet v1.0.0, 2025.
- DOI: `10.13026/3z8q-x658`
- Official page: `https://physionet.org/content/cgmacros/1.0.0/`

CGMacros contains data from 45 participants: 15 healthy, 16 with prediabetes, and 14 with type 2 diabetes. It includes Dexcom G6 Pro and Abbott FreeStyle Libre Pro CGM data, Fitbit activity/heart rate, meal macronutrients, demographics, anthropometrics and laboratory variables.

### Deployment demo subset

`data/demo/cgmacros_demo.csv` is generated from the real preprocessed CGMacros forecasting table. By default it contains one released participant from each HbA1c-derived dataset group (healthy, prediabetes and type 2 diabetes), with about 48 hours of usable observations per participant.

The exact selected IDs, released time ranges and row counts are recorded in `data/demo/cgmacros_demo.metadata.json`. Dates remain privacy-shifted exactly as released by the dataset authors.

To rebuild the subset from the full official dataset:

```bash
python scripts/build_demo_dataset.py --hours 48
```

See [`data/demo/README.md`](data/demo/README.md) and [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md) for attribution and licensing.

### 1. Download the official dataset

```bash
python scripts/download_cgmacros.py
```

The downloader:

1. downloads the official archive from the PhysioNet public distribution;
2. verifies the published SHA-256 checksum;
3. extracts to `data/raw/cgmacros/`;
4. keeps the full third-party dataset outside Git tracking.

### 2. Inspect the released sensor streams

```bash
python scripts/diagnose_cgmacros.py
```

An important implementation detail discovered during full-data validation is that the **released merged participant CSVs are aligned on a one-minute timestamp timeline**. The preprocessing code therefore infers the released cadence from each file and validates lags/targets by actual elapsed time instead of assuming native sensor cadence.

### 3. Build the forecasting table

```bash
python scripts/preprocess_cgmacros.py --glucose-source dexcom
```

Default output:

```text
data/processed/cgmacros_forecasting.csv.gz
```

The pipeline creates 30-minute forecasting samples with features including:

- current glucose;
- glucose lags at 15 and 30 minutes;
- recent glucose change;
- time-of-day cyclical features;
- carbohydrates/protein/fat/fiber in the previous 120 minutes;
- rolling heart rate, METs and activity calories;
- age, BMI, HbA1c, fasting glucose and fasting insulin.

Dexcom is the default selected glucose signal for the current benchmark. Libre can be evaluated separately:

```bash
python scripts/preprocess_cgmacros.py --glucose-source libre
```

### 4. Compare real-data models

Strict participant-level holdout:

```bash
python scripts/train_real_model.py --compare --split grouped
```

This keeps entire participants in either train or test rather than randomly mixing correlated measurements from the same person.

Train one grouped model:

```bash
python scripts/train_real_model.py --model hgb --split grouped
```

Train a personalized model for one participant using an earlier-70% / later-30% chronological split:

```bash
python scripts/train_real_model.py --model hgb --split personalized --participant 001
```

Benchmark the personalized HGB model across **all 45 participants**:

```bash
python scripts/benchmark_personalized.py --model hgb
```

The evaluation reports MAE, RMSE and a persistence baseline. Model artifacts and prediction CSV files are written locally to `artifacts/` and ignored by Git.

### 5. Explore a real participant in the dashboard

```bash
streamlit run app.py
```

Open the **🌍 Real CGMacros** tab, choose a participant, inspect the released CGM trajectory, and train the participant-specific +30-minute model interactively. The dashboard uses the full `data/processed/cgmacros_forecasting.csv.gz` when available and otherwise falls back to `data/demo/cgmacros_demo.csv`.

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

The Docker image includes only the small licensed `data/demo/` subset, not the full CGMacros archive. Mount a local `data/processed/` directory if you want the full preprocessed cohort inside the container; the dashboard automatically prefers the full table when present.

## Tests and quality

```bash
pytest -q
ruff check .
```

The normal CI uses small generated fixtures reproducing the CGMacros schema. The separate `CGMacros Full Benchmark` workflow downloads and verifies the official data, executes the full real-data benchmark and uploads only metric artifacts. The demo-subset builder is deterministic with respect to the preprocessed table and records its selected participants in metadata.

## Scientific scope

The project deliberately separates three claims:

1. **Synthetic simulator:** useful for software demonstration and what-if interaction, but not clinically validated physiology.
2. **Real-data forecasting:** trained/evaluated on the public CGMacros research dataset with leakage-aware splits, but still not a clinical model.
3. **Digital twin research direction:** a future validated system would require prospective evaluation, calibration, external cohorts, uncertainty estimation, subgroup analysis and clinical governance.

The project is inspired by established in-silico diabetes simulation work, but it is not the UVA/Padova simulator and makes no regulatory claim.

See [`docs/RESEARCH.md`](docs/RESEARCH.md), [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md), [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md), and [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md).

## Roadmap

- [x] MVP virtual-patient simulator
- [x] interactive dashboard
- [x] lifestyle what-if scenarios
- [x] synthetic ML baseline
- [x] FHIR export + REST API
- [x] automated tests / CI
- [x] official CGMacros downloader with checksum verification
- [x] real CGMacros preprocessing
- [x] full-data validation on all 45 participants
- [x] participant-level real-data baseline
- [x] personalized chronological baseline across all participants
- [x] real participant visualization in Streamlit
- [x] licensed real-data deployment demo subset
- [ ] repeated grouped cross-validation / leave-one-participant-out evaluation
- [ ] feature ablations and stronger temporal baselines
- [ ] calibrated predictive uncertainty
- [ ] external dataset validation
- [ ] subgroup/fairness analysis with adequate sample sizes
- [ ] prospective human-in-the-loop study protocol
- [ ] regulated medical-device pathway, only if the project ever moves beyond research

## Licensing

Repository source code: **MIT** — see [`LICENSE`](LICENSE).

CGMacros data and the derived files under `data/demo/`: **CC BY-NC-SA 4.0**, owned/licensed by the original rights holders and distributed/derived with attribution to PhysioNet CGMacros. The full raw dataset is not included in this repository. See [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md).
