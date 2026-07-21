# Distribution and Release Process

## Recommended method (immediate)

**Controlled internal wheel with recorded SHA-256**

1. Build wheel and sdist: `python -m build`
2. Record filenames and SHA-256 in `reports/packaging/ENG-PKG-001_Release_Manifest.json`
3. Store wheel in a controlled internal location (signed release folder or private artifact store)
4. Citizens pins exact version in `config/engine_version.yaml` and `pyproject.toml`

## Acceptable

- Private GitHub Releases on this repository
- Internal Python package index (devpi, Artifactory, Azure Artifacts)
- Direct wheel reference with SHA-256 verification

## Not acceptable

- Public PyPI without authorization
- Unversioned source directory installs for release validation
- Editable (`pip install -e`) installs as release artifact
- Floating Git branch dependencies
- Untrusted network shares without checksum verification

## Release checklist

1. Run `tests/engine_packaging/`
2. Build clean wheel + sdist
3. Clean-environment install test
4. Update `qla_core/CHANGELOG.md` and release notes
5. Publish manifest JSON with commit, hashes, test results
6. Notify client projects (Citizens Stage 4D)

## Citizens integration

After release, Citizens should:

1. Update `config/engine_version.yaml` with distribution name, exact version, wheel SHA-256
2. Pin `qla-enterprise-conversion-engine==0.1.0` in Citizens `pyproject.toml`
3. Re-run `tools/engine/check_engine_compatibility.py` — require PASS
