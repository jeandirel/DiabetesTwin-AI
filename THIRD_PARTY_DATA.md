# Third-party data

## CGMacros v1.0.0

DiabetesTwin-AI can optionally use the **CGMacros: a scientific dataset for personalized nutrition and diet monitoring** dataset distributed by PhysioNet.

### Attribution

Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A. *CGMacros: a scientific dataset for personalized nutrition and diet monitoring* (version 1.0.0). PhysioNet. 2025.

DOI: `10.13026/3z8q-x658`

Official source: `https://physionet.org/content/cgmacros/1.0.0/`

### License

The CGMacros files are licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** by their original rights holders.

The MIT license in this repository applies to the DiabetesTwin-AI source code. It does **not** relicense CGMacros data.

### Distribution policy in this repository

Raw and preprocessed CGMacros files are intentionally excluded from Git through `.gitignore`.

`scripts/download_cgmacros.py` downloads the original archive directly from PhysioNet and checks it against the SHA-256 hash published in PhysioNet's `SHA256SUMS.txt`:

```text
05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d
```

Users of the data are responsible for complying with the CGMacros license and for providing the required attribution in derivative work.

### Privacy note

The CGMacros authors state that full dates in the released CGM recordings and food photographs were shifted by a random number of days to protect privacy. DiabetesTwin-AI preserves the released timestamps and does not attempt to reverse that transformation.
