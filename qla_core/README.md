# qla_core — Enterprise Conversion Engine

Reusable LifePRO-to-QLAdmin conversion library. Import package name: `qla_core`.

Distribution: `qla-enterprise-conversion-engine` (see repository `pyproject.toml`).

This package is client-neutral. Client projects (Citizens, CSO, etc.) supply their own configuration, mappings, and source authority.

## Citizens-required rate API

- `qla_core.rate_dbf_schema`
- `qla_core.rate_factor_loader`
- `qla_core.rate_key_setup`
- `qla_core.rate_member_setup`
- `qla_core.rate_dbf_writer`

## Version metadata

```python
import qla_core
qla_core.__version__
qla_core.API_COMPATIBILITY_VERSION
```

## Optional dependencies

Install extras as needed:

- `pip install qla-enterprise-conversion-engine[dbf]` — DBF emit
- `pip install qla-enterprise-conversion-engine[crosswalk]` — Excel crosswalk load
- `pip install qla-enterprise-conversion-engine[converters]` — pandas/numpy converters
- `pip install qla-enterprise-conversion-engine[all]` — all optional runtime deps
