# Recreating the `eternal` conda environment

This folder contains files to help recreate the `eternal` conda environment used by this project.

Files:
- `environment.yml` — conda environment template (name: `eternal`).
- `requirements.txt` — optional pip-only package list.
- `recreate_env.sh` — small script to remove and recreate the conda env from `environment.yml`.

Quick usage

1. To create the environment (from this folder):

```bash
cd requirements
./recreate_env.sh
```

2. Activate the environment:

```bash
conda activate eternal
```

Exporting your exact current env (recommended)

If you still have the `eternal` env on your machine and want to capture the exact packages & versions, run:

```bash
conda activate eternal
conda env export --name eternal --no-builds > requirements/environment.yml
# review the generated file, then commit it to the repo
```

Platform/system package notes

- `pyzbar` typically requires the system zbar library. On Debian/Ubuntu install:
  `sudo apt install -y libzbar0`
- `pigpio` requires the `pigpiod` daemon on Raspberry Pi:
  `sudo apt install -y pigpio && sudo systemctl enable --now pigpiod`

If you want, I can export your `eternal` environment from your machine (if you run the export command) and update `environment.yml` with exact versions — tell me when you're ready.
