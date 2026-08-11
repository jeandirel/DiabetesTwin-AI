# CGMacros deployment demo subset

This directory contains a **small derived subset** of the public CGMacros v1.0.0 research dataset so the DiabetesTwin-AI dashboard can demonstrate real-CGM forecasting without downloading the full ~627 MB archive at runtime.

## Provenance

Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring* (version 1.0.0). PhysioNet. 2025.

- DOI: `10.13026/3z8q-x658`
- Official source: `https://physionet.org/content/cgmacros/1.0.0/`
- Dataset license: **CC BY-NC-SA 4.0**

## What is included

`cgmacros_demo.csv` is generated from the project's leakage-aware preprocessed forecasting table. By default the builder selects:

- one released participant from the healthy group;
- one released participant from the prediabetes group;
- one released participant from the type 2 diabetes group;
- the earliest 48-hour usable window for each selected participant.

The exact selected IDs, row counts, and released date ranges are recorded in `cgmacros_demo.metadata.json`.

The timestamps remain privacy-shifted exactly as released by the CGMacros authors. This project does not attempt to recover original dates.

## License boundary

The files in `data/demo/` that are derived from CGMacros are provided under **CC BY-NC-SA 4.0**, not the repository's MIT code license. The MIT license continues to apply to DiabetesTwin-AI source code.

This subset is intended for non-commercial research, education, and software demonstration in accordance with the source license. It is not clinical data collected by DiabetesTwin-AI and must not be used for treatment decisions.

## Rebuild

After downloading and preprocessing the official dataset:

```bash
python scripts/download_cgmacros.py
python scripts/preprocess_cgmacros.py --glucose-source dexcom
python scripts/build_demo_dataset.py
```
