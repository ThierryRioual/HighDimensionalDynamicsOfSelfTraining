# Historical research exports

The former `pdfs/` directory mixed reference PDFs, earlier experiment exports,
HTML exports, and copies of paper figures. Its files are preserved under
`legacy_exports/`, with their original names and contents. Earlier raster
figures from the manuscript are preserved under `manuscript_legacy_figures/`.
These local historical files are excluded from Git, as the original generated
exports were. They are not dependencies of the maintained experiments.

[`inventory.json`](inventory.json) records the original and relocated paths,
sizes, roles, and original SHA256 checksums. The inventory also records the
manuscript and audit moves. Compilation products may subsequently be regenerated;
the checksum is explicitly that of the file before the reorganization.

Current versioned paper figures live in `../manuscript/figures/`. New plot
previews live in `../outputs/figures/`. Historical filenames and dated audit
statements describe earlier snapshots and should not be interpreted as current
reproduction instructions. No historical scientific artifact was deleted.
