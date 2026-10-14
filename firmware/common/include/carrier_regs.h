/* Carrier MCU I2C register map - contract with software/tools/carrierctl.py (future MCU backend).
 * Mirrors docs/design/power-mcu.md sec. 2.1. Skeleton - values subject to change until v1.0. */
#ifndef CARRIER_REGS_H
#define CARRIER_REGS_H

#define CARRIER_I2C_ADDR        (0x42U)

#define REG_ID                  (0x00U)
#define REG_FW_MAJOR            (0x01U)
#define REG_FW_MINOR            (0x02U)
#define REG_STATE               (0x03U)
#define REG_SLOT_STATE_BASE     (0x04U)  /* 3 bytes */
#define REG_SLOT_CMD            (0x08U)
#define REG_RAIL_STATUS         (0x09U)
#define REG_WAKE_SRC            (0x0AU)
#define REG_IRQ_STATUS          (0x0BU)
#define REG_IRQ_MASK            (0x0CU)
#define REG_WDT_CFG             (0x10U)
#define REG_WDT_KICK            (0x11U)
#define REG_PARK_CFG            (0x18U)
#define REG_PARK_CMD            (0x19U)
#define REG_TIMING_BASE         (0x20U)
#define REG_FWUPD               (0x40U)
#define REG_HOST_PWR_STATE      (0x50U)
#define REG_HOST_PWR_CMD        (0x51U)
#define REG_HOST_BUSY           (0x52U)  /* lease seconds, max 600 */
#define REG_HOST_I_MEAS         (0x53U)
#define REG_SAFETY_STATUS       (0x58U)

#define HOST_BUSY_LEASE_MAX_S   (600U)

#endif /* CARRIER_REGS_H */
