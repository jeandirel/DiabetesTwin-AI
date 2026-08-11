# Verified CGMacros benchmark

Benchmark date: **2026-08-11**

This document records the first end-to-end benchmark of DiabetesTwin-AI on the official **PhysioNet CGMacros v1.0.0** release.

## Data provenance

- Dataset: *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*
- Source: PhysioNet v1.0.0
- DOI: `10.13026/3z8q-x658`
- Dataset license: **CC BY-NC-SA 4.0**
- Raw archive: `CGMacros_dateshifted365.zip`
- Verified SHA-256: `05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d`
- Participants found after extraction: **45**

The benchmark workflow downloads the archive from the official public PhysioNet distribution, verifies the checksum, extracts it, preprocesses the participant files, trains the baselines, and uploads only benchmark metrics as a GitHub Actions artifact. Raw CGMacros data are not committed to this repository.

## Important preprocessing finding

The released merged participant CSV files are aligned on a **one-minute timestamp timeline**. The first implementation incorrectly assumed native CGM sampling cadences when creating row-based lags and targets, which discarded most usable data.

The current implementation infers the sampling interval from each released participant file and validates the actual time difference for 15-minute/30-minute lags and the +30-minute target.

Full-release diagnostics observed:

- total merged rows across participant CSVs: **687,580**
- parsed timestamps: **687,580**
- Dexcom non-null rows: **629,825**
- Libre non-null rows: **687,360**
- Dexcom rows with a usable near +30-minute future value: **628,657**
- median gap in the released Dexcom series: **1 minute**
- median gap in the released Libre series: **1 minute**

## Forecasting table

After leakage-aware lag/target construction using Dexcom as the selected glucose source:

- usable forecasting rows: **621,069**
- participants: **45**
- horizon: **30 minutes**
- features: **18**

Features:

1. current glucose
2. glucose lag 15 minutes
3. glucose lag 30 minutes
4. glucose delta over 15 minutes
5. sine time-of-day
6. cosine time-of-day
7. carbohydrates in previous 120 minutes
8. protein in previous 120 minutes
9. fat in previous 120 minutes
10. fiber in previous 120 minutes
11. rolling heart rate over 30 minutes
12. rolling METs over 60 minutes
13. rolling activity calories over 60 minutes
14. age
15. BMI
16. HbA1c
17. fasting glucose
18. fasting insulin

## Cross-person evaluation

The grouped benchmark uses a participant-level holdout. Entire participants are assigned to train or test; neighboring CGM samples from the same person are therefore never split across both sets.

- train participants: **36**
- test participants: **9**
- train samples: **493,841**
- test samples: **127,228**

| Model | MAE (mg/dL) | RMSE (mg/dL) | Persistence MAE (mg/dL) |
|---|---:|---:|---:|
| Random Forest | **13.11** | **18.94** | 13.39 |
| HistGradientBoosting | 13.40 | 19.27 | 13.39 |

On this fixed participant split, Random Forest improves the simple persistence baseline by about **0.28 mg/dL MAE**. HistGradientBoosting is essentially tied with persistence and is slightly worse by 0.01 mg/dL.

This result should not be generalized beyond this split. A stronger study should use repeated/grouped cross-validation or leave-one-participant-out evaluation.

## Personalized evaluation

For each participant independently, the earlier **70%** of usable observations are used for training and the later **30%** for testing. The current benchmark uses HistGradientBoosting.

Across all 45 participants:

| Metric | Result |
|---|---:|
| Mean MAE | **12.63 mg/dL** |
| Median MAE | **12.05 mg/dL** |
| Mean RMSE | **17.97 mg/dL** |
| Median RMSE | **16.92 mg/dL** |
| Mean persistence MAE | **12.42 mg/dL** |
| Median persistence MAE | **11.83 mg/dL** |
| Mean MAE improvement vs persistence | **-0.21 mg/dL** |
| Median MAE improvement vs persistence | **-0.12 mg/dL** |
| Participants beating persistence | **20 / 45** |
| Participants tying persistence | **1 / 45** |

The personalized HGB baseline therefore **does not yet consistently beat persistence**. It is better for 20 participants, tied for one, and worse for the remainder.

That is an important scientific result: the project now has a real, leakage-aware benchmark, but the current feature/model combination is not strong enough to claim reliable personalized forecasting superiority.

## Interpretation

The benchmark validates the **software/data pipeline**, not clinical utility.

What is demonstrated:

- official data can be acquired reproducibly;
- all 45 released participants can be parsed;
- 621k+ real forecasting examples can be constructed;
- participant identifiers survive preprocessing without leakage-causing normalization bugs;
- models can be evaluated on unseen participants and chronologically within a participant;
- performance is compared against a strong naive persistence baseline.

What is **not** demonstrated:

- clinical safety or effectiveness;
- superiority across independent cohorts;
- robustness around hypoglycemia/hyperglycemia specifically;
- calibrated uncertainty;
- treatment or insulin-dosing capability;
- causal lifestyle effects.

## Next modeling experiments

The next improvements should prioritize methodology rather than adding a more complex neural network immediately:

1. repeated participant-level group splits / GroupKFold;
2. per-participant normalization and calibration;
3. explicit glucose trend/velocity/acceleration windows;
4. robust missingness indicators for Fitbit/lab features;
5. feature ablations: glucose-only vs +meals vs +activity vs +labs;
6. separate Dexcom and Libre benchmarks;
7. direct multi-horizon targets (15/30/60 minutes);
8. quantile or conformal prediction intervals;
9. only then compare sequence models such as LSTM/TCN/Transformer against the strong persistence and tree baselines;
10. external validation before any clinical-facing claim.

## Reproduction

```bash
python scripts/download_cgmacros.py
python scripts/diagnose_cgmacros.py
python scripts/preprocess_cgmacros.py --glucose-source dexcom
python scripts/train_real_model.py --compare --split grouped
python scripts/benchmark_personalized.py --model hgb
```

The GitHub Actions workflow `.github/workflows/cgmacros-benchmark.yml` executes the same full benchmark and stores the metrics as a short-lived artifact.
