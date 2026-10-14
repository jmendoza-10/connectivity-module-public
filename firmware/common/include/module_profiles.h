/* Per-module timing profiles (ms). Defaults from docs/power-reset-sequencing.md (rev 0.3).
 * EM92 = Sierra EM92XX PTS Rev 5, FN990 = Telit FN990 HDG Rev 3. Values marked U are engineering choices / unverified. */
#ifndef MODULE_PROFILES_H
#define MODULE_PROFILES_H

#include <stdint.h>

typedef struct {
    const char *name;
    uint32_t t_pg_timeout_ms;   /* PWR_EN -> PG (U) */
    uint32_t t_perst_ms;        /* PG -> PERST# release, EM92 T_pvpgl >= 150 ms */
    uint32_t t_enum_max_ms;     /* rescan window (U) */
    uint32_t t_shdn_ms;         /* FCPO# low -> power off if no indicator, EM92 max 12 s + margin */
    uint32_t t_reset_pulse_ms;  /* FN990 > 1 s, EM92 >= 450 ms */
    uint32_t t_off_ms;          /* off time before re-power (U) */
} module_profile_t;

extern const module_profile_t g_profile_em9291;
extern const module_profile_t g_profile_fn990a28;

#endif /* MODULE_PROFILES_H */
