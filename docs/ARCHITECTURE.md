# Architecture

## Goal

DiabetesTwin-AI is a **research and education prototype** combining an interactive synthetic virtual patient with a real-data forecasting pipeline based on PhysioNet CGMacros.

It intentionally does **not** recommend medication or insulin doses and is not a medical device.

## System view

```text
                                 REAL-DATA PATH

PhysioNet CGMacros v1.0.0
CGM + Fitbit + meals + bio/labs
            |
            v
  download + SHA256 verification
            |
            v
     schema-aware ingestion
            |
            v
30-min forecasting feature table
            |
      +-----+------------------------+
      |                              |
      v                              v
participant-level holdout       per-patient temporal split
      |                              |
      v                              v
HGB / Random Forest            HGB / Random Forest
      |                              |
      +-------------+----------------+
                    v
          observed vs predicted CGM
                    |
                    v
             Streamlit real-data tab


                               SYNTHETIC-TWIN PATH

Virtual patient profile
        |
        v
Lifestyle events -------> physiology-inspired simulation engine
                               |
                               +------> CGM-like 5-minute trajectory
                               |              |
                               |              +--> glucose reporting metrics
                               |              +--> Streamlit what-if dashboard
                               |              +--> FHIR Observation export
                               |
                               +------> synthetic longitudinal dataset
                                              |
                                              v
                                  HistGradientBoostingRegressor
                                      30-min software baseline

REST clients <---------- FastAPI /simulate and /fhir/observations
```

## Real-data ingestion

`src/diabetestwin/cgmacros.py` discovers the 45 participant CSV files recursively and follows the released CGMacros schema. Dexcom G6 Pro is the default glucose source because the study sampled it more frequently than Libre Pro; Libre can be selected explicitly.

The preprocessing layer creates a chronological feature table containing:

- current glucose;
- 15- and 30-minute glucose lags;
- recent glucose delta;
- cyclical time-of-day features;
- meal macronutrients observed in the previous 120 minutes;
- rolling Fitbit heart rate, METs, and activity calories;
- age, BMI, HbA1c, fasting glucose, and fasting insulin.

The target is glucose approximately 30 minutes later. Rows are removed when the future sample is not temporally compatible with the expected sensor interval.

## Leakage controls

Two evaluation modes are deliberately separated.

### Cross-person generalization

`train_grouped_real_predictor()` uses `GroupShuffleSplit` with the participant identifier as the group. A participant can therefore appear in **either** train **or** test, never both.

This is much stricter than randomly splitting CGM rows because adjacent samples from the same individual are strongly correlated.

### Personalized digital-twin forecasting

`train_personalized_real_predictor()` selects one participant and performs a chronological split: the earlier 70% of usable samples train the model and the later 30% evaluate it.

This approximates the intended digital-twin setting: learn from an individual's history and forecast subsequent measurements without training on future samples.

## Synthetic twin

The synthetic path is kept for interactive counterfactual demonstrations where a user changes meals, physical activity, sleep, or stress. The simulator is intentionally transparent and simple. It is **not** claimed to reproduce validated human physiology.

The synthetic model and real-data model are shown separately in the interface so software-demo performance cannot be confused with measured real-data performance.

## Interoperability

The existing FHIR export is currently attached to synthetic trajectories. A future extension can map consented/research CGM data to FHIR `Observation` resources while preserving source provenance and research-use restrictions.

## Data and licensing boundary

The code repository is MIT licensed. The CGMacros files are third-party data licensed separately under CC BY-NC-SA 4.0. Raw or preprocessed CGMacros files are ignored by Git and are downloaded directly from PhysioNet by the user.

See `THIRD_PARTY_DATA.md` for attribution and restrictions.

## Production / clinical evolution

Moving beyond a research prototype would require at minimum:

1. prospective data collection under an approved protocol;
2. external validation on independent cohorts and sites;
3. calibrated predictive uncertainty;
4. missing-data and sensor-failure handling;
5. subgroup and fairness analysis with sufficient sample sizes;
6. model/data versioning and auditability;
7. privacy, security, and clinical governance;
8. formal medical-device/regulatory assessment before any diagnostic or treatment use.
