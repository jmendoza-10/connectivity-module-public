# Coding rules

- **MISRA C:2012** (with Amendments 1-4 where the checker supports them) is mandatory for `boot/`, `app/`, `common/`.
  Required rules: no deviations. Advisory rules: deviations allowed with a documented rationale in `docs/misra-deviations.md`.
- ISO 26262-6 ASIL-B practices: no dynamic memory after init, no recursion, bounded loops, defensive checks on all external
  inputs (I2C registers, NVM), explicit state-machine tables, every output write followed by a read-back where the hardware allows.
- Vendor code (NXP RTD/SAF) is treated as a qualified/third-party component; do not modify it in place.
- Every requirement ID (SG/TSR/SWR) referenced in code comments for traceability.
