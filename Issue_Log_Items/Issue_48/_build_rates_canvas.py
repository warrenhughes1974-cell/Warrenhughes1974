"""Generate Issue #48 primary/secondary rates canvas."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
EVID = ROOT / "Issue_Log_Items" / "Issue_48" / "evidence"
OUT = Path(
    r"C:\Users\warren\.cursor\projects\c-Users-warren-Documents-GitHub-Warrenhughes1974"
    r"\canvases\issue48-primary-secondary-rates.canvas.tsx"
)


def fmt(n: int) -> str:
    return f"{n:,}" if n else "—"


def main() -> None:
    inv = list(
        csv.DictReader(
            (EVID / "issue48_primary_secondary_rate_inventory.csv").open(encoding="utf-8")
        )
    )
    typ = list(
        csv.DictReader(
            (EVID / "issue48_primary_secondary_type_summary.csv").open(encoding="utf-8")
        )
    )

    type_rows = [
        [
            r["type_code"],
            r["secondary_coverage_count"],
            fmt(int(r["secondary_rows"])),
            r["primary_coverage_count"],
            fmt(int(r["primary_rows"])),
            r["both"],
            r["secondary_only"],
            r["primary_only"],
        ]
        for r in typ
    ]
    inv_rows = [
        [
            r["coverage_id"],
            r["type_code"],
            fmt(int(r["secondary_rate_table_rows"])),
            fmt(int(r["primary_paagerat_rows"])),
            r["present_in"].replace("_", " "),
        ]
        for r in inv
    ]

    content = f"""import {{
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Stack,
  Stat,
  Table,
  Text,
}} from "cursor/canvas";

const TYPE_ROWS: string[][] = {json.dumps(type_rows)};

const INVENTORY_ROWS: string[][] = {json.dumps(inv_rows)};

export default function Issue48PrimarySecondaryRates() {{
  return (
    <Stack gap={{24}} style={{{{ padding: 24 }}}}>
      <Stack gap={{8}}>
        <H1>Primary vs Secondary Rate Inventory</H1>
        <Text tone="secondary">
          Primary = PAAGERAT (attained-age). Secondary = Rate_Table_Extract_Txt
          (age x duration). Counts are coverage + rate-type keys and source row
          counts. Source: Issue #48 extracts, 2026-07-10.
        </Text>
      </Stack>

      <Grid columns={{4}} gap={{12}}>
        <Stat value="1,128,984" label="Secondary total rows" />
        <Stat value="24,424" label="Primary total rows" />
        <Stat value="212" label="Secondary coverage+type keys" />
        <Stat value="148" label="Primary coverage+type keys" />
      </Grid>

      <Callout tone="info" title="How to read this">
        SECONDARY ONLY means the rate type exists in the Rate Table file but not
        under that same coverage ID in PAAGERAT. PRIMARY ONLY means it exists in
        PAAGERAT only. Row counts are not directly comparable across files
        (different grain).
      </Callout>

      <Card>
        <CardHeader>Rate type summary</CardHeader>
        <CardBody style={{{{ padding: 0 }}}}>
          <Table
            stickyHeader
            striped
            headers={{[
              "Type",
              "Secondary coverages",
              "Secondary rows",
              "Primary coverages",
              "Primary rows",
              "Both",
              "Secondary only",
              "Primary only",
            ]}}
            columnAlign={{[
              "left",
              "right",
              "right",
              "right",
              "right",
              "right",
              "right",
              "right",
            ]}}
            rows={{TYPE_ROWS}}
          />
        </CardBody>
      </Card>

      <Divider />

      <Stack gap={{8}}>
        <H2>Full coverage + rate-type listing (358 keys)</H2>
        <Text tone="secondary">
          Every coverage ID and rate type found in either file, with row counts
          in each.
        </Text>
      </Stack>

      <Card>
        <CardHeader>Inventory</CardHeader>
        <CardBody style={{{{ padding: 0 }}}}>
          <Table
            stickyHeader
            striped
            headers={{[
              "Coverage ID",
              "Type",
              "Secondary rows",
              "Primary rows",
              "Present in",
            ]}}
            columnAlign={{["left", "left", "right", "right", "left"]}}
            rows={{INVENTORY_ROWS}}
          />
        </CardBody>
      </Card>
    </Stack>
  );
}}
"""
    OUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
