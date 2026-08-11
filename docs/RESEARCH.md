# Scientific grounding and research plan

Last reviewed: 2026-08-11.

## 1. CGM reporting

The dashboard reports the standard glucose bands used in the American Diabetes Association's **Standards of Care in Diabetes—2026** for most adults using CGM:

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

A 2026 randomized pilot reported a human-in-the-loop predictive digital-twin workflow for type 2 diabetes using longitudinal glucose, food, activity, and weight data, with the model periodically retrained as new patient data accrued. That direction motivates the future architecture here: longitudinal personalization + explicit human/clinical oversight.

Reference: Wang J et al. *Human-in-the-loop AI predictive digital twin to extend virtual precision diabetes care between visits*. npj Health Systems. 2026;3:59.

## 4. Candidate real-world dataset

PhysioNet CGMacros v1.0.0 is open access and includes data from 45 participants (15 healthy adults, 16 with prediabetes, 14 with type 2 diabetes), with CGM, known meal macronutrients, physical activity, demographics and additional health measurements across ten days.

Reference: Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring*. PhysioNet. 2025. doi:10.13026/3z8q-x658.

## 5. Interoperability

FHIR `Observation` is the HL7 resource for patient measurements such as blood glucose. The project exports synthetic glucose points as minimal FHIR R5 Observation resources using LOINC 15074-8 and UCUM `mg/dL`.

Reference: HL7 FHIR R5, `Observation` resource and glucose example.

## 6. Recommended next research phase

1. Freeze this synthetic MVP and document assumptions.
2. Build a CGMacros ingestion notebook/pipeline without committing the 600+ MB dataset to Git.
3. Define patient-level splits and a baseline persistence model.
4. Compare linear/GBDT/sequence models with MAE, RMSE and clinically stratified errors.
5. Add uncertainty estimation and calibration.
6. Personalize using transfer learning or patient-specific fine-tuning.
7. Run ablations for meal/activity/sleep/stress features.
8. Add model/data cards, privacy assessment and human-in-the-loop review.
9. Only after formal validation, consider any clinical-study interface.
