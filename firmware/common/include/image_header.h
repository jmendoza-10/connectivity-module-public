/* Application image header verified by the bootloader via HSE (signature over header + payload). Skeleton. */
#ifndef IMAGE_HEADER_H
#define IMAGE_HEADER_H

#include <stdint.h>

#define IMAGE_MAGIC (0x57574331UL) /* "WWC1" */

typedef struct {
    uint32_t magic;
    uint32_t header_version;
    uint32_t fw_version;          /* major<<16 | minor<<8 | patch */
    uint32_t rollback_counter;    /* compared with HSE monotonic counter */
    uint32_t payload_size;
    uint8_t  payload_sha256[32];
    uint8_t  signature[64];       /* ECDSA P-256 (r||s), key in HSE key catalog */
} image_header_t;

#endif /* IMAGE_HEADER_H */
