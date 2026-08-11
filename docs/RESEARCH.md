# Scientific grounding and research plan

Last reviewed: 2026-08-11.

## 1. CGM reporting

The dashboard reports common glucose bands used in the American Diabetes Association's **Standards of Care in Diabetes—2026** for many adults using CGM:

- time in range (TIR): 70–180 mg/dL;
- below range: <70 mg/dL;
- level 2 hypoglycemia: <54 mg/dL;
- above range: >180 mg/dL;
- level 2 hyperglycemia: >250 mg/dL.

The app displays these as reporting bands only. Individual clinical goals must be personalized by qualified clinicians.

Reference: American Diabetes Association Professional Practice Committee. *6. Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: Standards of Care in Diabetes—2026*. Diabetes Care. 2026;49(Suppl 1):S132–S149.

## 2. Why simulate a virtual patient?

The UVA/Padova Type 1 Diabetes Simulator established the scientific value of in-silico virtual populations for testing diabetes algorithms. Its 2013 update was accepted by the FDA for certain preclinical closed-loop investigations. DiabetesTwin-AI does not reproduce or claim equivalence to UVA/Padova; it uses the same general principle of explicit virtual-patient simulation for software prototyping.

Reference: Visentin R, Dalla Man C, Kovatchev B, Cobelli C. *The University of Virginia/Padova type 1 diabetes simulator matches the glucose traces of a clinical trial*. Diabetes Technology & Therapeutics. 2014;16(7):428-434. doi:10.1089/dia.2013.0377.

## 3. Recent digital-twin evidence

A 2026 randomized pilot reported a human-in-the-loop predictive digital-twin workflow for type 2 diabetes using longitudinal glucose, food, activity, and weight data, with the model periodically retrained as new patient data accrued. That direction motivates the architecture here: longitudinal personalization plus explicit human/clinical oversight.

Reference: Wang J et al. *Human-in-the-loop AI predictive digital twin to extend virtual precision diabetes care between visits*. npj Health Systems. 2026;3:59.

## 4. Real-world dataset now integrated

PhysioNet **CGMacros v1.0.0** is the real-data foundation implemented in this repository. It contains data from 45 participants: 15 healthy adults, 16 with prediabetes, and 14 with type 2 diabetes, with approximately ten days of monitoring per participant.

The study includes:

- Abbott FreeStyle Libre Pro CGM;
- Dexcom G6 Pro CGM;
- Fitbit Sense heart rate and activity variables;
- breakfast, lunch and dinner timestamps;
- meal calories, carbohydrates, protein, fat and fiber;
- demographics and anthropometrics;
- HbA1c, fasting glucose, insulin and lipid laboratory variables;
- food photographs and microbiome-related supplementary files.

Reference: Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*. PhysioNet. 2025. doi:10.13026/3z8q-x658.

The raw archive is not committed because it is roughly 627 MB and carries its own **CC BY-NC-SA 4.0** license. The repository downloader fetches it from PhysioNet and verifies the published SHA-256 checksum.

During full-release validation, the merged participant CSV files were observed to use a one-minute timestamp timeline. The preprocessing implementation now infers released cadence and validates lags/targets by elapsed time rather than assuming native sensor cadence.

## 5. Forecasting question

The implemented supervised task is:

> Given the participant's current/recent glucose, time of day, recent meal macronutrients, recent activity/heart-rate context, and available baseline characteristics, what is the measured glucose approximately 30 minutes later?

The task is deliberately framed as forecasting, not treatment recommendation.

## 6. Leakage-aware evaluation

CGM points from one person are highly autocorrelated. A random row split would therefore produce overly optimistic estimates.

The project implements two evaluation settings:

1. **Participant holdout:** entire people are separated between train and test with `GroupShuffleSplit`.
2. **Personalized temporal holdout:** for one participant, the earlier 70% of usable observations trains the model and the later 30% is held out.

Every real-data evaluation also reports a simple persistence baseline: current glucose used as the +30-minute forecast.

## 7. Current real-data models and verified benchmark

Two transparent classical baselines are implemented:

- HistGradientBoostingRegressor;
- RandomForestRegressor.

The full checksum-verified CGMacros release produced **621,069 usable forecasting rows across all 45 participants**.

For one participant-level split with 36 people in train and 9 unseen people in test:

- Random Forest MAE: **13.11 mg/dL**, RMSE: **18.94 mg/dL**;
- HistGradientBoosting MAE: **13.40 mg/dL**, RMSE: **19.27 mg/dL**;
- persistence MAE: **13.39 mg/dL**.

For participant-specific HistGradientBoosting models using a chronological 70/30 split across all 45 participants:

- mean MAE: **12.63 mg/dL**;
- median MAE: **12.05 mg/dL**;
- mean persistence MAE: **12.42 mg/dL**;
- personalized HGB beat persistence for **20 of 45** participants and tied for one.

The current personalized baseline therefore does **not** demonstrate consistent superiority over persistence. This is a useful negative/neutral result that motivates stronger validation and model design rather than inflated claims.

Detailed benchmark methodology and results are in [`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md).

## 8. Interoperability

FHIR `Observation` is the HL7 resource for patient measurements such as blood glucose. The project currently exports synthetic glucose points as minimal FHIR R5 Observation resources using LOINC 15074-8 and UCUM `mg/dL`.

Reference: HL7 FHIR R5, `Observation` resource and glucose example.

## 9. Research milestones

Completed:

1. synthetic virtual-patient simulator;
2. interactive lifestyle what-if dashboard;
3. synthetic forecasting software baseline;
4. official CGMacros download/checksum pipeline;
5. schema-aware real-data preprocessing;
6. validation of the full release across all 45 participants;
7. 621k+ leakage-aware +30-minute forecasting rows;
8. participant-level holdout baselines;
9. personalized chronological benchmark across all participants;
10. persistence baseline comparison;
11. real CGM visualization and +30-minute prediction overlay.

Next scientifically meaningful work:

1. repeated participant-level GroupKFold / leave-one-participant-out evaluation;
2. quantify errors by participant and glycemic region, not only aggregate MAE/RMSE;
3. evaluate Dexcom and Libre separately;
4. add calibrated predictive intervals;
5. perform feature ablations for glucose history, meals, Fitbit variables and static clinical variables;
6. add missingness indicators and improve handling of participant-specific all-missing Fitbit variables;
7. test richer temporal features and only then compare sequence models against persistence/tree baselines;
8. externally validate on an independent public or prospectively collected cohort;
9. define subgroup/fairness analyses with adequate statistical power;
10. create a prospective human-in-the-loop research protocol before any clinical-facing extension.
