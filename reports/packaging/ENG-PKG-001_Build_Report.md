# ENG-PKG-001 Build Report

**Timestamp:** 2026-07-12T15:28:57Z  
**Result:** PASS

## Build environment

| Field | Value |
|-------|-------|
| Python | `3.14.4` |
| Command | `python -m build` |
| Commit | `0ed59cdc472c10c0189d5328883460fdc5fb0189` |

## Artifacts

| Artifact | Filename | SHA-256 |
|----------|----------|---------|
| Wheel | `qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl` | `320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674` |
| Source dist | `qla_enterprise_conversion_engine-0.1.0.tar.gz` | `ca70a4bbc338f45aabaca6d6b8dcb2898bc8632c80705370096ac941831ba80c` |

## Wheel inspection

- Files in wheel: 57
- Prohibited content: none detected
- Contents list: `ENG-PKG-001_Distribution_Contents.txt`

## Source-tree tests

```
..........                                                               [100%]
10 passed in 0.17s

```

## Installed-package tests (clean venv)

```
..........                                                               [100%]
10 passed in 0.67s

```

## Clean install smoke

Result: **PASS**

```
OK

```

## Build stderr

```
WARNING Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=61
  - wheel
* Getting build dependencies for sdist...
For maximum compatibility please make sure to include a `scheme` prefix in your URL (e.g. 'http://'). Given value: docs/packaging/PUBLIC_API_CONTRACT.md
C:\Users\warren\AppData\Local\Temp\build-env-9vy90clq\Lib\site-packages\setuptools\config\_apply_pyprojecttoml.py:82: SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
  corresp(dist, value, root_dir)
* Installed build dependency versions:
  - setuptools==83.0.0
  - wheel==0.47.0
* Building sdist...
For maximum compatibility please make sure to include a `scheme` prefix in your URL (e.g. 'http://'). Given value: docs/packaging/PUBLIC_API_CONTRACT.md
C:\Users\warren\AppData\Local\Temp\build-env-9vy90clq\Lib\site-packages\setuptools\config\_apply_pyprojecttoml.py:82: SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
  corresp(dist, value, root_dir)
warning: sdist: standard file not found: should have one of README, README.rst, README.txt, README.md

* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=61
  - wheel
* Getting build dependencies for wheel...
For maximum compatibility please make sure to include a `scheme` prefix in your URL (e.g. 'http://'). Given value: docs/packaging/PUBLIC_API_CONTRACT.md
C:\Users\warren\AppData\Local\Temp\build-env-spbphuzx\Lib\site-packages\setuptools\config\_apply_pyprojecttoml.py:82: SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
  corresp(dist, value, root_dir)
* Installed build dependency versions:
  - setuptools==83.0.0
  - wheel==0.47.0
* Building wheel...
For maximum compatibility please make sure to include a `scheme` prefix in your URL (e.g. 'http://'). Given value: docs/packaging/PUBLIC_API_CONTRACT.md
C:\Users\warren\AppData\Local\Temp\build-env-spbphuzx\Lib\site-packages\setuptools\config\_apply_pyprojecttoml.py:82: SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
  corresp(dist, value, root_dir)

```
