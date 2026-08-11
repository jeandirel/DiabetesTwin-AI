from diabetestwin.models import ExerciseEvent, LifestyleScenario, MealEvent, PatientProfile
from diabetestwin.simulator import simulate_day


def test_simulator_is_reproducible_and_bounded():
    patient = PatientProfile.from_phenotype("balanced")
    scenario = LifestyleScenario(meals=[MealEvent(hour=12, carbs_g=60)])
    first = simulate_day(patient, scenario, seed=123)
    second = simulate_day(patient, scenario, seed=123)
    assert first.equals(second)
    assert len(first) == 288
    assert first["glucose_mg_dl"].between(45, 400).all()


def test_meal_raises_and_activity_reduces_excursion():
    patient = PatientProfile.from_phenotype("balanced")
    meal_only = LifestyleScenario(meals=[MealEvent(hour=12, carbs_g=80)], stress=0)
    meal_activity = LifestyleScenario(
        meals=[MealEvent(hour=12, carbs_g=80)],
        exercise=[ExerciseEvent(hour=12.5, duration_min=45, intensity=0.8)],
        stress=0,
    )
    a = simulate_day(patient, meal_only, seed=5)
    b = simulate_day(patient, meal_activity, seed=5)
    post = (a["hour"] >= 12.5) & (a["hour"] <= 15.0)
    assert b.loc[post, "glucose_mg_dl"].mean() < a.loc[post, "glucose_mg_dl"].mean()
