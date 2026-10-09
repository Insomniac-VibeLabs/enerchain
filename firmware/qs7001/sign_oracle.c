/* QS7001 OTP image, reference. This is not a host stack.
 * The part is personalized once, the image hash is published with the
 * meter public key, and field update is not a command.
 *
 * SPI mode 0, MSB first, this die is the slave. EC-MINT1 is the only master.
 * Command 0xA1: 32-byte canonical message, then CRC-8 (poly 0x07, init 0)
 * over those 32 bytes. On a CRC match, ML-DSA-44-sign and clock out
 * 2420 signature bytes. Any other payload is ignored.
 * Command 0x5C 0x5C: erase the private key, then stop answering.
 * No other command produces a signature.
 *
 * The private key is generated on this die and is not readable.
 */
#include <stdint.h>
#include <stddef.h>

#define MSG_LEN 32
#define SIG_LEN 2420

extern void qs_mldsa44_keygen(void);          /* on-die, once, result stays */
extern void qs_mldsa44_sign(const uint8_t m[MSG_LEN], uint8_t sig[SIG_LEN]);
extern void qs_key_erase(void);
extern int qs_spi_read(uint8_t *b);            /* 0 on CS deassert */
extern void qs_spi_write(uint8_t b);

static uint8_t crc8(const uint8_t *p, size_t n) {
    uint8_t c = 0;
    for (size_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++)
            c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x07) : (uint8_t)(c << 1);
    }
    return c;
}

static int wiped;

void sign_oracle_boot(void) {
    qs_mldsa44_keygen();
    wiped = 0;
}

void sign_oracle_poll(void) {
    uint8_t cmd;
    if (wiped)
        return;
    if (!qs_spi_read(&cmd))
        return;
    if (cmd == 0x5C) {
        uint8_t second = 0;
        if (qs_spi_read(&second) && second == 0x5C) {
            qs_key_erase();
            wiped = 1;
        }
        return;
    }
    if (cmd != 0xA1)
        return;
    uint8_t msg[MSG_LEN];
    for (int i = 0; i < MSG_LEN; i++) {
        if (!qs_spi_read(&msg[i]))
            return;
    }
    uint8_t crc = 0;
    if (!qs_spi_read(&crc) || crc != crc8(msg, MSG_LEN))
        return;
    uint8_t sig[SIG_LEN];
    qs_mldsa44_sign(msg, sig);
    for (int i = 0; i < SIG_LEN; i++)
        qs_spi_write(sig[i]);
}
