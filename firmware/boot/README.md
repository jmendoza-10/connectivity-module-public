# Secure bootloader (stub)

Verified by HSE at reset (Secure Memory Region). Selects slot A/B by header version + "confirmed" flag + boot counter, verifies
the image signature via HSE, enforces the rollback counter, jumps. See docs/design/power-mcu.md sec. 5. Not implemented.
