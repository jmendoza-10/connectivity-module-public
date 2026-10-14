# HSE key provisioning and device lifecycle (outline)

> **Roadmap proposal (not implemented)**

**No private keys, passwords or per-device secrets are ever committed to this repository.**

1. Offline HSM generates the OEM firmware-signing key pair (ECDSA P-256 proposed). Public key exported.
2. Factory station: install NXP HSE firmware; program the HSE key catalog with the public key; configure Secure Memory Region /
   Core Reset tables so HSE verifies the bootloader before core release; program bootloader + application slot A.
3. Inject per-device keys (host-link authentication) and record serial -> key ID in the factory database (not in git).
4. Advance device lifecycle to production/in-field; lock debug (password-protected or disabled).
5. Verify: boot, read SAFETY_STATUS, attempt an unsigned image (must be rejected).

Exact HSE service names, lifecycle states and debug-lock options are in NXP HSE documentation (NDA) [U].
