# Architecture

## Goal

DiabetesTwin-AI is a **research and education prototype** for exploring how a personalized virtual patient's glucose trajectory can react to meal, activity, sleep, and stress scenarios.

It intentionally does **not** recommend medication or insulin doses and is not a medical device.

## Components

```text
Virtual patient profile
        |
        v
Lifestyle events -------> Physiology-inspired simulation engine
                               |
                               +------> CGM-like 5-minute trajectory
                               |              |
                               |              +--> ADA-style reporting metrics
                               |              +--> Streamlit dashboard
                               |              +--> FHIR Observation export
                               |
                               +------> Synthetic longitudinal dataset
                                              |
                                              v
                                  HistGradientBoostingRegressor
                                      30-min prediction demo

REST clients <---------- FastAPI /simulate and /fhir/observations
```

## Why a hybrid architecture?

A useful digital twin needs more than a black-box predictor. The repository separates:

1. **State and interventions** — patient parameters + lifestyle events.
2. **Mechanistic prior** — transparent response kernels for meals, exercise, circadian rhythm, stress, and sleep.
3. **Data-driven layer** — a gradient-boosted model trained on synthetic longitudinal trajectories.
4. **Observation layer** — standardized CGM metrics and FHIR-compatible export.

This supports rapid prototyping while making the assumptions visible.

## Production evolution

For a real study, replace the synthetic generator with consented/approved patient data, define a prospective protocol, calibrate per patient, quantify uncertainty, validate on unseen patients and sites, document subgroup performance, and establish clinical governance before any clinical use.
