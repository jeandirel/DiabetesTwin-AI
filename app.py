from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from diabetestwin.fhir import dataframe_to_fhir_observations
from diabetestwin.metrics import HIGH, LOW, compute_glycemic_metrics
from diabetestwin.models import ExerciseEvent, LifestyleScenario, MealEvent, PatientProfile
from diabetestwin.predictor import train_virtual_patient_predictor
from diabetestwin.simulator import simulate_day


st.set_page_config(page_title="DiabetesTwin-AI", page_icon="🧬", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
      [data-testid="stMetricValue"] {font-size: 1.7rem;}
      .dt-card {border:1px solid rgba(128,128,128,.22); border-radius:18px; padding:16px 18px;}
      .dt-note {font-size:.9rem; opacity:.78;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧬 DiabetesTwin-AI")
st.caption("Personalized Diabetes Monitoring Twin · predictive virtual patient · lifestyle what-if simulation")
st.warning(
    "Educational/research prototype using synthetic virtual-patient data. It does not provide medical advice, "
    "diagnosis, medication or insulin-dosing recommendations."
)

with st.sidebar:
    st.header("Virtual patient")
    phenotype = st.selectbox(
        "Phenotype",
        ["balanced", "insulin_resistant", "active"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    preset = PatientProfile.from_phenotype(phenotype)
    name = st.text_input("Name", "Twin-01")
    baseline = st.slider("Baseline glucose (mg/dL)", 75, 190, int(preset.baseline_glucose))
    carb_sens = st.slider("Carbohydrate sensitivity", 0.20, 1.50, float(preset.carb_sensitivity), 0.05)
    activity_sens = st.slider("Activity sensitivity", 5.0, 40.0, float(preset.activity_sensitivity), 1.0)
    patient = preset.model_copy(
        update={
            "name": name,
            "baseline_glucose": float(baseline),
            "carb_sensitivity": float(carb_sens),
            "activity_sensitivity": float(activity_sens),
        }
    )

    st.divider()
    st.header("Lifestyle scenario")
    breakfast = st.slider("Breakfast carbs (g)", 0, 120, 45, 5)
    lunch = st.slider("Lunch carbs (g)", 0, 150, 65, 5)
    dinner = st.slider("Dinner carbs (g)", 0, 150, 70, 5)
    exercise_minutes = st.slider("Evening activity (min)", 0, 90, 35, 5)
    exercise_intensity = st.slider("Activity intensity", 0.0, 1.0, 0.55, 0.05)
    stress = st.slider("Stress level", 0.0, 1.0, 0.25, 0.05)
    sleep_hours = st.slider("Sleep duration (h)", 4.0, 10.0, 7.5, 0.25)
    sleep_quality = st.slider("Sleep quality", 0.0, 1.0, 0.80, 0.05)

scenario = LifestyleScenario(
    meals=[
        MealEvent(hour=8.0, carbs_g=breakfast, label="Breakfast"),
        MealEvent(hour=13.0, carbs_g=lunch, label="Lunch"),
        MealEvent(hour=19.5, carbs_g=dinner, label="Dinner"),
    ],
    exercise=(
        [ExerciseEvent(hour=18.0, duration_min=exercise_minutes, intensity=exercise_intensity, label="Activity")]
        if exercise_minutes > 0
        else []
    ),
    stress=stress,
    sleep_hours=sleep_hours,
    sleep_quality=sleep_quality,
)

baseline_scenario = LifestyleScenario(
    meals=[
        MealEvent(hour=8.0, carbs_g=45, label="Breakfast"),
        MealEvent(hour=13.0, carbs_g=65, label="Lunch"),
        MealEvent(hour=19.5, carbs_g=70, label="Dinner"),
    ],
    exercise=[ExerciseEvent(hour=18.0, duration_min=35, intensity=0.55, label="Activity")],
    stress=0.25,
    sleep_hours=7.5,
    sleep_quality=0.8,
)

frame = simulate_day(patient, scenario, seed=42)
baseline_frame = simulate_day(patient, baseline_scenario, seed=42)
metrics = compute_glycemic_metrics(frame)
baseline_metrics = compute_glycemic_metrics(baseline_frame)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(
    "Mean glucose",
    f"{metrics.mean_glucose:.0f} mg/dL",
    f"{metrics.mean_glucose - baseline_metrics.mean_glucose:+.0f}",
)
m2.metric(
    "Time in range",
    f"{metrics.time_in_range_pct:.1f}%",
    f"{metrics.time_in_range_pct - baseline_metrics.time_in_range_pct:+.1f} pp",
)
m3.metric("Below 70", f"{metrics.time_below_range_pct:.1f}%")
m4.metric("Above 180", f"{metrics.time_above_range_pct:.1f}%")
m5.metric("Variability (CV)", f"{metrics.coefficient_of_variation_pct:.1f}%")

monitor_tab, whatif_tab, model_tab, interoperability_tab = st.tabs(
    ["📈 Monitor", "🧪 What-if", "🤖 Predictive model", "🔗 FHIR export"]
)

with monitor_tab:
    fig = go.Figure()
    fig.add_hrect(y0=LOW, y1=HIGH, opacity=0.10, line_width=0, annotation_text="70–180 mg/dL range")
    fig.add_trace(
        go.Scatter(
            x=frame["hour"],
            y=frame["glucose_mg_dl"],
            mode="lines",
            name="Personalized twin",
            line=dict(width=3),
        )
    )
    for meal in scenario.meals:
        fig.add_vline(x=meal.hour, opacity=0.25, line_dash="dot")
    for activity in scenario.exercise:
        fig.add_vline(x=activity.hour, opacity=0.25, line_dash="dash")
    fig.update_layout(
        height=470,
        xaxis_title="Hour of day",
        yaxis_title="Glucose (mg/dL)",
        legend_title="Trajectory",
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "The shaded 70–180 mg/dL band is a standardized CGM reporting range used in ADA 2026 guidance; "
        "individual clinical targets must be set with a healthcare professional."
    )

with whatif_tab:
    compare = pd.DataFrame(
        {
            "hour": frame["hour"],
            "Current scenario": frame["glucose_mg_dl"],
            "Reference lifestyle": baseline_frame["glucose_mg_dl"],
        }
    )
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(x=compare["hour"], y=compare["Reference lifestyle"], mode="lines", name="Reference")
    )
    fig2.add_trace(
        go.Scatter(
            x=compare["hour"],
            y=compare["Current scenario"],
            mode="lines",
            name="What-if",
            line=dict(width=3),
        )
    )
    fig2.update_layout(
        height=430,
        xaxis_title="Hour",
        yaxis_title="Glucose (mg/dL)",
        margin=dict(l=20, r=20, t=25, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)
    delta_peak = metrics.max_glucose - baseline_metrics.max_glucose
    delta_tir = metrics.time_in_range_pct - baseline_metrics.time_in_range_pct
    st.info(
        f"Scenario effect (simulation): peak glucose {delta_peak:+.1f} mg/dL and "
        f"time-in-range {delta_tir:+.1f} percentage points "
        "versus the reference lifestyle. These are model outputs, not predicted treatment outcomes."
    )

with model_tab:

    @st.cache_resource(show_spinner="Training the virtual-patient predictor…")
    def get_model(phenotype_name: str, baseline_value: float, carb_value: float, activity_value: float):
        p = PatientProfile.from_phenotype(phenotype_name).model_copy(
            update={
                "baseline_glucose": baseline_value,
                "carb_sensitivity": carb_value,
                "activity_sensitivity": activity_value,
            }
        )
        return train_virtual_patient_predictor(p, days=28, seed=7)

    predictor = get_model(phenotype, float(baseline), float(carb_sens), float(activity_sens))
    e = predictor.evaluation
    c1, c2, c3 = st.columns(3)
    c1.metric("30-min MAE", f"{e.mae_mg_dl:.2f} mg/dL")
    c2.metric("30-min RMSE", f"{e.rmse_mg_dl:.2f} mg/dL")
    c3.metric("Test samples", f"{e.test_samples:,}")
    st.markdown(
        "The prediction layer uses a **HistGradientBoostingRegressor** trained on synthetic trajectories "
        "generated by the same virtual-patient engine. "
        "The split is temporal by simulated day to reduce leakage between adjacent CGM points."
    )
    st.caption(
        "This performance is only a software validation on synthetic data. It must not be interpreted as "
        "clinical accuracy. "
        "A real study should retrain and externally validate on consented CGM/lifestyle data (e.g. PhysioNet CGMacros)."
    )

with interoperability_tab:
    observations = dataframe_to_fhir_observations(frame.iloc[::3].reset_index(drop=True))
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in observations],
    }
    st.write("FHIR R5-compatible demonstration export of synthetic glucose observations.")
    st.json(bundle["entry"][0]["resource"])
    st.download_button(
        "Download FHIR Bundle JSON",
        data=json.dumps(bundle, indent=2),
        file_name="diabetestwin_fhir_bundle.json",
        mime="application/fhir+json",
    )

st.divider()
st.caption(
    "DiabetesTwin-AI · student research prototype · synthetic data by default · no medication recommendations · "
    "scientific references and limitations are documented in the repository."
)
