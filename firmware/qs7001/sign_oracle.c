/* QS7001 signing oracle, v0.0.1 (doc-1.4). Reference image, not a host stack.
 *
 * The part is personalized once at the factory, before the cover is sealed:
 * the provisioning flow calls sign_oracle_personalize(), which generates two
 * ML-DSA keys on this die (the meter key in slot 0, the tamper key in slot
 * 1), binds the meter id and role, and stores a "personalized" flag in
 * non-volatile memory. Both public keys are read out by the vendor
 * provisioning interface and published with the image hash in the meter
 * certificate. Field update is not a command.
 *
 * doc-1.1 called keygen from the boot routine and kept the wipe flag in RAM,
 * so every power cycle produced a new, uncertified key and a wiped part came
 * back to life. Both are now persistent.
 *
 * SPI mode 0, MSB first, this die is the slave. EC-MINT1 is the only master.
 *   A1, 32-byte record of kind 0, CRC-8 (poly 0x07, init 0) over the record.
 *     Signed with the meter key. While the signature is computed, the SPI
 *     idle fill returns 00. Then 5A followed by SIG_LEN signature bytes, or
 *     EE if refused.
 *   5C 5C: erase the meter key, record the wipe. Signing token records ends.
 *   A7, 32-byte record of kind 1, CRC-8: accepted once, only after a wipe
 *     and only in the same powered session. Signed with the tamper key,
 *     which is erased before the signature is released. This is how the
 *     ledger learns that the cover was opened under power, as opposed to a
 *     meter that went quiet or was revoked (docs/grid-operator.md).
 * Any other byte is ignored. No command produces a key or a signature over
 * anything but a 32-byte record in the format below.
 *
 * Record (big-endian): id[4] {ver=1,role}[1] class[1] seq[4] e_exp[6]
 *   e_imp[6] tokens[6] cal_crc16[2] kind[1] zero[1].
 * Roles: 1 GEN, 2 GRID, 3 LOAD.
 *
 * Rollback guard: the oracle signs only a record whose seq is strictly
 * greater than the last one it signed and whose three counters do not go
 * backward, and only if tokens * 1000 <= e_exp. The last signed values are
 * written to non-volatile memory before the signature is released, so a
 * rolled-back FRAM on the board cannot get a lower count signed again.
 *
 * The tamper record passes the same guard, so it cannot carry lower counts
 * than the last token record.
 *
 * GPIO3 is ZEROIZE from the tamper latch. It is checked on every poll, so
 * the meter key is erased even if EC-MINT1 never sends 5C 5C. A wiped part
 * that boots with its tamper key unused erases it then: the tamper record
 * can only be made while the wipe's own power session lasts, which the
 * board's signer-rail delay holds open for about 1.3 s
 * (hardware/fab/ec-seal1/CIRCUITS.md).
 *
 * The qs_* functions are the vendor SDK surface this image needs. Names are
 * placeholders; the QS7001 SDK is under NDA and the mapping is open item O-3
 * in docs/open-items.md.
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#ifndef SIG_LEN
#define SIG_LEN 2420            /* ML-DSA-44. 4627 if only ML-DSA-87 is offered. */
#endif
#define MSG_LEN 32
#define Q_WH 1000ULL
#define NV_MAGIC 0x45433031u    /* "EC01" */
#define KEY_METER 0
#define KEY_TAMPER 1
#define KIND_TOKEN 0
#define KIND_TAMPER 1

/* Two key slots on the part; whether the QS7001 offers two is open item O-3. */
extern void qs_mldsa_keygen(int slot);                   /* on-die, result stays */
extern void qs_mldsa_sign(int slot, const uint8_t m[MSG_LEN], uint8_t sig[SIG_LEN]);
extern void qs_key_erase(int slot);
extern int  qs_spi_read(uint8_t *b);                     /* 0 on CS deassert */
extern void qs_spi_write(uint8_t b);
extern void qs_spi_set_idle_fill(uint8_t b);
extern int  qs_gpio_read(int pin);
extern int  qs_nv_read(void *buf, size_t len);           /* 0 on success */
extern int  qs_nv_write(const void *buf, size_t len);    /* atomic, 0 on success */

struct nv_state {
    uint32_t magic;
    uint8_t  personalized;
    uint8_t  wiped;
    uint8_t  role;
    uint8_t  tamper_key;        /* 1 while the tamper key exists */
    uint32_t meter_id;
    uint32_t last_seq;
    uint64_t last_exp;
    uint64_t last_imp;
    uint64_t last_tok;
};

static struct nv_state nv;

static uint8_t crc8(const uint8_t *p, size_t n) {
    uint8_t c = 0;
    for (size_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++)
            c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x07) : (uint8_t)(c << 1);
    }
    return c;
}

static uint64_t be(const uint8_t *p, int n) {
    uint64_t v = 0;
    for (int i = 0; i < n; i++)
        v = (v << 8) | p[i];
    return v;
}

static void nv_load(void) {
    if (qs_nv_read(&nv, sizeof nv) != 0 || nv.magic != NV_MAGIC) {
        memset(&nv, 0, sizeof nv);
        nv.magic = NV_MAGIC;
    }
}

static void wipe(void) {
    qs_key_erase(KEY_METER);
    nv.wiped = 1;
    qs_nv_write(&nv, sizeof nv);
}

static void tamper_key_erase(void) {
    qs_key_erase(KEY_TAMPER);
    nv.tamper_key = 0;
    qs_nv_write(&nv, sizeof nv);
}

/* Factory only, through the vendor provisioning interface. Never reachable
 * from the EC-MINT1 SPI. Returns 0 on success, -1 if already personalized. */
int sign_oracle_personalize(uint32_t meter_id, uint8_t role) {
    nv_load();
    if (nv.personalized || nv.wiped || role < 1 || role > 3)
        return -1;
    qs_mldsa_keygen(KEY_METER);
    qs_mldsa_keygen(KEY_TAMPER);
    nv.personalized = 1;
    nv.tamper_key = 1;
    nv.meter_id = meter_id;
    nv.role = role;
    nv.last_seq = 0;
    nv.last_exp = nv.last_imp = nv.last_tok = 0;
    return qs_nv_write(&nv, sizeof nv) == 0 ? 0 : -1;
}

void sign_oracle_boot(void) {
    nv_load();
    qs_spi_set_idle_fill(0x00);
    if (nv.wiped && nv.tamper_key)
        tamper_key_erase();     /* the wipe's power session is over */
    if (!nv.wiped && qs_gpio_read(3))
        wipe();
}

/* Returns 1 if the record may be signed. */
static int record_ok(const uint8_t m[MSG_LEN], uint8_t kind) {
    uint32_t id = (uint32_t)be(m, 4);
    uint8_t ver = m[4] >> 4, role = m[4] & 0x0F;
    uint32_t seq = (uint32_t)be(m + 6, 4);
    uint64_t e_exp = be(m + 10, 6), e_imp = be(m + 16, 6), tok = be(m + 22, 6);
    if (id != nv.meter_id || ver != 1 || role != nv.role || m[5] != 0x22)
        return 0;
    if (m[30] != kind || m[31] != 0)
        return 0;
    if (seq <= nv.last_seq)
        return 0;
    if (e_exp < nv.last_exp || e_imp < nv.last_imp || tok < nv.last_tok)
        return 0;
    if (tok * Q_WH > e_exp)
        return 0;
    return 1;
}

void sign_oracle_poll(void) {
    uint8_t cmd, kind;
    int slot;
    if (!nv.personalized || (nv.wiped && !nv.tamper_key))
        return;
    if (!nv.wiped && qs_gpio_read(3)) {
        wipe();
        return;
    }
    if (!qs_spi_read(&cmd))
        return;
    if (cmd == 0x5C) {
        uint8_t second = 0;
        if (qs_spi_read(&second) && second == 0x5C && !nv.wiped)
            wipe();
        return;
    }
    if (cmd == 0xA1 && !nv.wiped) {
        kind = KIND_TOKEN;
        slot = KEY_METER;
    } else if (cmd == 0xA7 && nv.wiped) {
        kind = KIND_TAMPER;
        slot = KEY_TAMPER;
    } else
        return;
    uint8_t msg[MSG_LEN];
    for (int i = 0; i < MSG_LEN; i++) {
        if (!qs_spi_read(&msg[i]))
            return;
    }
    uint8_t crc = 0;
    if (!qs_spi_read(&crc) || crc != crc8(msg, MSG_LEN))
        return;
    if (!record_ok(msg, kind)) {
        qs_spi_write(0xEE);
        return;
    }
    nv.last_seq = (uint32_t)be(msg + 6, 4);
    nv.last_exp = be(msg + 10, 6);
    nv.last_imp = be(msg + 16, 6);
    nv.last_tok = be(msg + 22, 6);
    if (qs_nv_write(&nv, sizeof nv) != 0) {
        qs_spi_write(0xEE);
        return;
    }
    static uint8_t sig[SIG_LEN];
    qs_mldsa_sign(slot, msg, sig);
    if (slot == KEY_TAMPER)
        tamper_key_erase();     /* one tamper record, ever */
    qs_spi_write(0x5A);
    for (int i = 0; i < SIG_LEN; i++)
        qs_spi_write(sig[i]);
}
