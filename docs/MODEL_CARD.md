# Model Card — DiabetesTwin-AI v0.2

## Intended use

Student research, software demonstration, interactive education, and prototyping of a personalized glucose digital-twin workflow.

## Not intended for

- diagnosis or screening;
- emergency decisions;
- medication or insulin dose selection;
- replacing a CGM, physician, diabetes educator, or validated medical device;
- claims about clinical benefit.

## Two model families

DiabetesTwin-AI deliberately separates **synthetic simulation** from **real-data forecasting**.

### 1. Synthetic digital-twin engine

The simulator produces a 24-hour glucose-like trajectory at five-minute resolution from:

- personalized baseline glucose;
- carbohydrate sensitivity;
- activity sensitivity;
- circadian amplitude;
- stress and sleep parameters;
- meal carbohydrate events;
- physical-activity events.

Effects are represented with simple transparent response kernels plus correlated noise. This is a physiology-inspired model, **not** a validated physiological simulator such as UVA/Padova.

A `HistGradientBoostingRegressor` can learn 30-minute-ahead glucose from synthetic trajectories. Its MAE/RMSE is a software-control metric only.

### 2. Real CGMacros forecasting

The real-data layer uses PhysioNet **CGMacros v1.0.0**, downloaded separately from the source repository. CGMacros contains 45 participants spanning healthy, prediabetes, and type 2 diabetes groups.

The forecasting features include:

- current glucose;
- 15- and 30-minute glucose lags;
- 15-minute glucose change;
- cyclical time of day;
- meal carbohydrates, protein, fat, and fiber in the prior 120 minutes;
- rolling Fitbit heart rate, METs, and activity calories;
- age, BMI, HbA1c, fasting glucose, and fasting insulin.

The target is glucose approximately 30 minutes later.

Two scikit-learn baselines are included:

- `HistGradientBoostingRegressor`;
- `RandomForestRegressor`.

Missing numeric features are median-imputed inside the training pipeline.

## Evaluation strategies

### Participant-level holdout

For cross-person evaluation, `GroupShuffleSplit` keeps each participant completely inside train or test. This reduces leakage from highly correlated neighboring CGM measurements.

Reported metrics:

- MAE in mg/dL;
- RMSE in mg/dL;
- persistence MAE, where current glucose is used as the naive +30-minute forecast;
- train/test sample counts;
- train/test participant counts.

### Personalized chronological holdout

For a participant-specific digital twin, the earlier 70% of the participant's usable timeline is used for training and the later 30% for testing.

This is a retrospective research evaluation, not a prospective clinical study.

## Data provenance

Source: Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*. PhysioNet, version 1.0.0, 2025.

DOI: `10.13026/3z8q-x658`

Dataset license: **CC BY-NC-SA 4.0**.

The repository does not redistribute CGMacros. The downloader obtains the official archive from PhysioNet and verifies the published SHA-256 checksum.

Dates in CGMacros are privacy-shifted by the data providers. DiabetesTwin-AI does not attempt to recover original dates.

## Limitations

- CGMacros is small for modern personalized forecasting: 45 participants.
- The cohort is not an external clinical validation cohort for this project.
- Treatment variables such as insulin dosing are not modeled here.
- Static demographics/labs can be incomplete.
- Missing and irregular sensor observations can reduce usable forecasting rows.
- Performance may differ substantially by participant, diabetes status, sensor, behavior, and time period.
- A 30-minute regression error alone is insufficient for clinical safety evaluation, especially near hypo/hyperglycemic ranges.
- The current models do not provide calibrated predictive uncertainty.

## Validation still required before any clinical claim

- prospective evaluation;
- external validation on independent cohorts/sites;
- calibrated uncertainty and coverage testing;
- subgroup/fairness analysis with adequate statistical power;
- robustness to sensor dropouts and distribution shift;
- clinically meaningful error analysis around hypo/hyperglycemia;
- privacy, security, consent, governance, and regulatory assessment.

## Safety statement

No output from this project should be used to change medication, insulin, diet, or treatment without a qualified healthcare professional. The repository is a research prototype, not a medical device.
