# Third-party data

## CGMacros v1.0.0

DiabetesTwin-AI can use the **CGMacros: a scientific dataset for personalized nutrition and diet monitoring** dataset distributed by PhysioNet.

### Attribution

Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring* (version 1.0.0). PhysioNet. 2025.

DOI: `10.13026/3z8q-x658`

Official source: `https://physionet.org/content/cgmacros/1.0.0/`

### License

The CGMacros files are licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** by their original rights holders.

The MIT license in this repository applies to the DiabetesTwin-AI source code. It does **not** relicense CGMacros data or derivatives of those data.

### Distribution policy in this repository

The **full raw and full preprocessed CGMacros datasets** are intentionally excluded from Git through `.gitignore`.

For deployment and classroom demonstrations, this repository includes a small derived subset under `data/demo/`. That subset remains under **CC BY-NC-SA 4.0** and includes its own attribution notice. By default the builder selects one released participant from each HbA1c-derived dataset group and approximately 48 hours of usable forecasting observations per selected participant.

`scripts/download_cgmacros.py` downloads the original archive directly from PhysioNet and checks it against the SHA-256 hash published in PhysioNet's `SHA256SUMS.txt`:

```text
05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d
```

`scripts/build_demo_dataset.py` creates the deployment subset from the project's full preprocessed forecasting table and records the selected participant IDs, released date ranges and row counts in `data/demo/cgmacros_demo.metadata.json`.

Users of the data are responsible for complying with the CGMacros license and for preserving the required attribution and ShareAlike terms in derivative data distributions.

### Privacy note

The CGMacros authors state that full dates in the released CGM recordings and food photographs were shifted by a random number of days to protect privacy. DiabetesTwin-AI preserves the released timestamps and does not attempt to reverse that transformation.

The participant identifiers contained in the demo subset are the pseudonymous identifiers already used in the public CGMacros release; DiabetesTwin-AI does not attempt to link them to real identities.
