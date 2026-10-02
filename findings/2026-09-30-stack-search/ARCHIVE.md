# Deprecated stack and timed-proof tooling

Decision: 2026-09-30. This research workflow is deprecated for routine layout
cleanup audits. Keep the Python modules, C++ search engine, tests and proof
dependency file; do not delete them. They remain useful building blocks and
can investigate a specific disputed result. Deprecation does not disable the
CLIs or change their semantics.

The next task is the [intended-flow inheritance checker](../../plans/2026-09-30-cleanup-generator.md#intended-flow-inheritance-audit-author-approved),
tracked in [todos](../../todos.md). It follows intended layer-addition paths,
compares inherited bindings per button, recommends clear/block for competing
non-Base bindings, and handles lightweight-cover upper-layer checks separately.
It was built on 2026-10-01 ([record](../2026-10-01-intended-flow-checker/README.md)).
Exhaustive timer proofs are not a prerequisite.

## Preserved checkpoint

[research-checkpoint-90.6.tar.gz](research-checkpoint-90.6.tar.gz) contains:

- The final default 90.6 certificate, summary and compact witness archive.
- Four readable per-layer reports and their JSON counterparts.
- The 531-test passing regression log.
- The 23 exploratory Python scripts formerly stored only under `out/`.
  These are historical experiments with hard-coded paths, not supported CLIs;
  some need intermediate data not included in this compact archive.

The recorded result is 11,491 witnessed, 31,644 excluded and 3,769 unresolved
alternatives. The 901 invariants passed 3,409 validation checks. These are
model-relative historical results, not complete answers or hardware certification.
The input remains `versions/neptune/90.6/single-set-default_hold-gyro_90.6.json`.

## Deleting out

`out/` is ignored by Git and contains generated search data and experiments;
no tracked layout or implementation lives there. After this archive is saved,
its contents may be deleted. That discards resumable large searches,
intermediate experiments and local full reports. Those searches would need to
be run again if wanted. The new intended-flow checker does not depend on them.
Historical documentation links into `out/` will stop working until restored
or regenerated. No deletion was performed as part of this deprecation.

To restore the compact checkpoint from the repository root:

```sh
tar -xzf findings/2026-09-30-stack-search/research-checkpoint-90.6.tar.gz
```

This restores the saved files beneath `out/`, including the evidence and
certificate used by the historical `timed_audit show` command. It does not
restore the large search databases or every intermediate report.
