/* Host test for sign_oracle.c. Stubs the QS7001 SDK surface with an SPI
 * byte script, a RAM "non-volatile" store, and a fake signer, then checks
 * the oracle's rules. Build and run:
 *   cc -std=c99 -Wall -Wextra -DSIG_LEN=8 -I.. -o /tmp/t \
 *      firmware/qs7001/test/test_sign_oracle.c && /tmp/t
 */
#define SIG_LEN 8
#include "../sign_oracle.c"
#include <stdio.h>
#include <stdlib.h>

/* ---- stubs ------------------------------------------------------------ */
static uint8_t in_buf[256];
static int in_len, in_pos;
static uint8_t out_buf[256];
static int out_len;
static uint8_t nv_store[sizeof(struct nv_state)];
static int nv_valid;
static int keygens, erases, key_present, tamper_present, gpio3;
static int tamper_signs, tamper_erases;

void qs_mldsa_keygen(int slot) {
    if (slot == KEY_METER) { keygens++; key_present = 1; }
    else tamper_present = 1;
}
void qs_mldsa_sign(int slot, const uint8_t m[MSG_LEN], uint8_t sig[SIG_LEN]) {
    if (slot == KEY_TAMPER) {
        if (!tamper_present) { printf("FAIL sign with an erased tamper key\n"); exit(1); }
        tamper_signs++;
    } else if (!key_present) { printf("FAIL sign with an erased meter key\n"); exit(1); }
    for (int i = 0; i < SIG_LEN; i++)
        sig[i] = (uint8_t)(m[i % MSG_LEN] ^ i ^ 0xA5);
}
void qs_key_erase(int slot) {
    if (slot == KEY_METER) { erases++; key_present = 0; }
    else { tamper_erases++; tamper_present = 0; }
}
int qs_spi_read(uint8_t *b) {
    if (in_pos >= in_len) return 0;
    *b = in_buf[in_pos++];
    return 1;
}
void qs_spi_write(uint8_t b) { out_buf[out_len++] = b; }
void qs_spi_set_idle_fill(uint8_t b) { (void)b; }
int qs_gpio_read(int pin) { return pin == 3 ? gpio3 : 0; }
int qs_nv_read(void *buf, size_t len) {
    if (!nv_valid) return -1;
    memcpy(buf, nv_store, len);
    return 0;
}
int qs_nv_write(const void *buf, size_t len) {
    memcpy(nv_store, buf, len);
    nv_valid = 1;
    return 0;
}

/* ---- helpers ---------------------------------------------------------- */
static int fails;
#define CHECK(c, what) do { if (!(c)) { fails++; printf("FAIL %s\n", what); } } while (0)

static void put(uint8_t *p, uint64_t v, int n) {
    for (int i = n - 1; i >= 0; i--) { p[i] = (uint8_t)v; v >>= 8; }
}

static void record(uint8_t m[MSG_LEN], uint32_t id, uint8_t role, uint32_t seq,
                   uint64_t e_exp, uint64_t e_imp, uint64_t tok) {
    memset(m, 0, MSG_LEN);
    put(m, id, 4);
    m[4] = (uint8_t)(0x10 | role);
    m[5] = 0x22;
    put(m + 6, seq, 4);
    put(m + 10, e_exp, 6);
    put(m + 16, e_imp, 6);
    put(m + 22, tok, 6);
    m[28] = 0x46; m[29] = 0x61;
}

/* Send one A1 (or A7) transaction; return the first response byte (0 if none). */
static uint8_t send(uint8_t cmd, const uint8_t m[MSG_LEN], uint8_t crc_xor) {
    in_len = 0; in_pos = 0; out_len = 0;
    in_buf[in_len++] = cmd;
    memcpy(in_buf + in_len, m, MSG_LEN);
    in_len += MSG_LEN;
    in_buf[in_len++] = (uint8_t)(crc8(m, MSG_LEN) ^ crc_xor);
    sign_oracle_poll();
    return out_len ? out_buf[0] : 0;
}

static uint8_t sign(const uint8_t m[MSG_LEN], uint8_t crc_xor) {
    return send(0xA1, m, crc_xor);
}

static void wipe_cmd(void) {
    in_len = 2; in_pos = 0; out_len = 0;
    in_buf[0] = 0x5C; in_buf[1] = 0x5C;
    sign_oracle_poll();
}

static void power_cycle(void) {
    memset(&nv, 0, sizeof nv); /* RAM is lost */
    sign_oracle_boot();
}

int main(void) {
    uint8_t m[MSG_LEN];

    /* Unpersonalized part signs nothing. */
    sign_oracle_boot();
    record(m, 0x42, 2, 1, 10000, 0, 10);
    CHECK(sign(m, 0) == 0, "unpersonalized part is silent");

    /* Personalize once. */
    CHECK(sign_oracle_personalize(0x42, 2) == 0, "personalize");
    CHECK(sign_oracle_personalize(0x42, 2) == -1, "second personalize refused");
    CHECK(keygens == 1, "one keygen");

    /* Boot does not regenerate the key. */
    power_cycle();
    power_cycle();
    CHECK(keygens == 1, "boot does not call keygen");

    /* A good record is signed: 5A then SIG_LEN bytes. */
    CHECK(sign(m, 0) == 0x5A && out_len == 1 + SIG_LEN, "first record signed");
    CHECK(out_buf[1] == (uint8_t)(m[0] ^ 0 ^ 0xA5), "signature bytes follow 5A");

    /* Replay of the same sequence is refused. */
    CHECK(sign(m, 0) == 0xEE, "replayed seq refused");

    /* Bad CRC is ignored. */
    record(m, 0x42, 2, 2, 20000, 0, 20);
    CHECK(sign(m, 0x01) == 0, "bad CRC ignored");

    /* Counter rollback is refused even with a fresh seq. */
    record(m, 0x42, 2, 2, 9000, 0, 9);
    CHECK(sign(m, 0) == 0xEE, "counter rollback refused");

    /* Token count above the energy is refused. */
    record(m, 0x42, 2, 2, 20000, 0, 21);
    CHECK(sign(m, 0) == 0xEE, "tokens above e_exp/1000 refused");

    /* Wrong meter id or role is refused. */
    record(m, 0x43, 2, 2, 20000, 0, 20);
    CHECK(sign(m, 0) == 0xEE, "wrong id refused");
    record(m, 0x42, 1, 2, 20000, 0, 20);
    CHECK(sign(m, 0) == 0xEE, "wrong role refused");

    /* The last signed state survives a power cycle. */
    record(m, 0x42, 2, 2, 20000, 500, 20);
    CHECK(sign(m, 0) == 0x5A, "seq 2 signed");
    power_cycle();
    CHECK(sign(m, 0) == 0xEE, "seq 2 refused after power cycle");
    record(m, 0x42, 2, 3, 30000, 500, 30);
    CHECK(sign(m, 0) == 0x5A, "seq 3 signed after power cycle");

    /* A record whose kind byte says tamper is not a token record. */
    record(m, 0x42, 2, 4, 30000, 500, 30);
    m[30] = 1;
    CHECK(sign(m, 0) == 0xEE, "A1 refuses a kind-1 record");
    CHECK(send(0xA7, m, 0) == 0, "A7 ignored before a wipe");

    /* Wipe by command: the meter key goes, the tamper key signs once. */
    wipe_cmd();
    CHECK(erases == 1 && !key_present, "5C 5C erased the key");
    CHECK(tamper_present, "tamper key kept for this power session");
    record(m, 0x42, 2, 4, 30500, 500, 30);
    CHECK(sign(m, 0) == 0, "A1 silent after the wipe");
    CHECK(send(0xA7, m, 0) == 0xEE, "A7 refuses a kind-0 record");
    m[30] = 1;
    record(m, 0x42, 2, 3, 30500, 500, 30); m[30] = 1;
    CHECK(send(0xA7, m, 0) == 0xEE, "tamper record must advance seq");
    record(m, 0x42, 2, 4, 29000, 500, 29); m[30] = 1;
    CHECK(send(0xA7, m, 0) == 0xEE, "tamper record cannot roll counters back");
    record(m, 0x42, 2, 4, 30500, 500, 30); m[30] = 1;
    CHECK(send(0xA7, m, 0) == 0x5A && out_len == 1 + SIG_LEN, "tamper record signed");
    CHECK(tamper_signs == 1 && !tamper_present && tamper_erases == 1,
          "tamper key erased after one signature");
    record(m, 0x42, 2, 5, 30500, 500, 30); m[30] = 1;
    CHECK(send(0xA7, m, 0) == 0, "second tamper record: silent");
    power_cycle();
    record(m, 0x42, 2, 4, 40000, 500, 40);
    CHECK(sign(m, 0) == 0, "wiped part silent after power cycle");
    CHECK(sign_oracle_personalize(0x42, 2) == -1, "wiped part cannot be re-personalized");

    /* Wipe by GPIO3 (ZEROIZE) on a fresh part. */
    memset(nv_store, 0, sizeof nv_store); nv_valid = 0; memset(&nv, 0, sizeof nv);
    erases = 0;
    sign_oracle_boot();
    CHECK(sign_oracle_personalize(7, 1) == 0, "personalize second part");
    gpio3 = 1;
    record(m, 7, 1, 1, 1000, 0, 1);
    CHECK(sign(m, 0) == 0, "ZEROIZE high: no signature");
    CHECK(erases == 1, "ZEROIZE erased the key");
    gpio3 = 0;
    tamper_erases = 0;
    power_cycle();
    CHECK(tamper_erases == 1 && !tamper_present, "unused tamper key erased at the next boot");
    CHECK(sign(m, 0) == 0, "still silent after ZEROIZE released and power cycle");
    m[30] = 1;
    CHECK(send(0xA7, m, 0) == 0, "no tamper record after a power cycle");

    /* A LOAD meter (role 3) can be personalized; role 4 cannot. */
    memset(nv_store, 0, sizeof nv_store); nv_valid = 0; memset(&nv, 0, sizeof nv);
    sign_oracle_boot();
    CHECK(sign_oracle_personalize(9, 4) == -1, "role 4 refused");
    CHECK(sign_oracle_personalize(9, 3) == 0, "LOAD role personalized");
    record(m, 9, 3, 1, 1000, 0, 1);
    CHECK(sign(m, 0) == 0x5A, "LOAD record signed");

    if (fails == 0)
        printf("PASS sign_oracle: one keygen, persistent wipe, rollback guard, one tamper record\n");
    return fails ? 1 : 0;
}
