/* State-machine interfaces - see firmware/docs/state-machines.md. Skeleton. */
#ifndef FSM_H
#define FSM_H

#include <stdint.h>

typedef enum { CAR_OFF = 0, CAR_BOOT, CAR_RAILS_UP, CAR_RUN, CAR_PARK, CAR_SHUTDOWN, CAR_FAULT } carrier_state_t;
typedef enum { S_OFF = 0, S_PWR, S_BOOT, S_LINK, S_UP, S_SHDN, S_RESET, S_FAULT } slot_state_t;
typedef enum { H_OFF = 0, H_ON, H_ALIVE, H_WARN, H_RESET, H_CUT, H_SHDN, H_FAULT } host_state_t;

void carrier_fsm_step(uint32_t now_ms);
void slot_fsm_step(uint8_t slot, uint32_t now_ms);
void host_fsm_step(uint32_t now_ms);

#endif /* FSM_H */
