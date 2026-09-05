# Environment

[Contents](../README.md)

The project uses Python 3.14.7 and Pipenv. The exact Python version is declared in `Pipfile`; dependencies are locked in `Pipfile.lock`. Configuration loading uses `toml==0.10.2`.

[Python 3.14.7](https://www.python.org/downloads/release/python-3147/) is a stable release dated August 5, 2026. Setup was verified with Pipenv 2026.8.0; the created environment contains pip 26.2.1.

## Windows setup

After installing Python 3.14.7, install Pipenv if needed:

```powershell
py -3.14 -m pip install pipenv==2026.8.0
```

Run from the project root:

```powershell
$env:PIPENV_VENV_IN_PROJECT = "1"
$env:PIPENV_IGNORE_VIRTUALENVS = "1"
py -3.14 -m pipenv sync
```

The environment is created in the project's `.venv` directory, which is excluded from Git. Set the variables above in each new setup session. Track both `Pipfile` and `Pipfile.lock` in Git.

## Running and verification

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
py -3.14 -m pipenv --venv
py -3.14 -m pipenv verify
py -3.14 -m pipenv run python --version
```

Select `.venv\Scripts\python.exe` as the IDE interpreter. Activation is optional when invoking the interpreter directly or using `pipenv run`.

Add new dependencies through Pipenv with exact versions and update `Pipfile.lock` alongside `Pipfile`. Install project packages only in this project's local environment.

## Configuration

`src/settings.py` reads the local `src/config.toml`, falling back to `src/default_config.toml` if it is absent. Neither TOML file contains settings yet. Loading uses `toml==0.10.2`, pinned in Pipenv.

The local `src/config.toml` is excluded from Git. After cloning, copy `src/default_config.toml` to that path if needed. Keep shared defaults in the template and local settings in `config.toml`. The local file replaces the template entirely; values are not merged.
