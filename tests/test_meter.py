"""EC-MINT1 / QS7001 reference model: the rules the hardware enforces."""

import pytest

from enerchain import crypto
from enerchain.meter import (RESEND_S, EcMint1, EnergyMeter, Fram, SignerOracle,
                             calibration_image)
from enerchain.record import (KIND_TAMPER, KIND_TOKEN, ROLE_GEN, ROLE_GRID, ROLE_LOAD,
                              MeterRecord, RecordError, crc8, crc16)


def make(q=10, every=2, role=ROLE_GRID, mid=7):
    s = SignerOracle(q=q)
    s.personalize(mid, role)
    m = EcMint1(fram=Fram(), signer=s, q=q, sign_every=every)
    m.provision(calibration_image(mid, role, [b"\x01\x02"]))
    return m


def test_crc_reference_values():
    assert crc8(b"123456789") == 0xF4          # CRC-8/SMBUS check value
    assert crc16(b"123456789") == 0x29B1       # CRC-16/CCITT-FALSE check value


def test_record_roundtrip_and_reserved_bytes():
    r = MeterRecord(1, ROLE_GEN, 5, 12345, 67, 12, 0xBEEF)
    raw = r.pack()
    assert len(raw) == 32 and MeterRecord.unpack(raw) == r
    with pytest.raises(RecordError):
        MeterRecord.unpack(raw[:30] + b"\x00\x01")
    with pytest.raises(RecordError):
        MeterRecord.unpack(raw[:30] + b"\x02\x00")         # no kind 2
    with pytest.raises(RecordError):
        MeterRecord(1, 1, 1, 1 << 48, 0, 0, 0).pack()
    t = MeterRecord(1, ROLE_GEN, 6, 12345, 67, 12, 0xBEEF, kind=KIND_TAMPER)
    assert t.pack()[30] == 1 and MeterRecord.unpack(t.pack()) == t


def test_blank_meter_does_not_count():
    m = EcMint1(fram=Fram(), signer=SignerOracle())
    m.pulse_export(5000)
    assert m.e_exp == 0 and not m.locked


def test_empty_transcript_does_not_arm():
    m = EcMint1(fram=Fram(), signer=SignerOracle())
    image = bytearray(calibration_image(1, ROLE_GEN, [b"\x00"]))
    image[7] = 0
    m.provision(bytes(image))
    m.pulse_export(100)
    assert m.locked and not m.armed and m.e_exp == 0


def test_one_token_per_q_and_record_every_n():
    m = make(q=10, every=2)
    m.pulse_export(19)
    assert m.tokens == 1 and not m.records
    m.pulse_export(1)
    assert m.tokens == 2 and len(m.records) == 1
    r = m.records[0].parsed
    assert (r.seq, r.e_exp, r.e_imp, r.tokens) == (1, 20, 0, 2)


def test_import_cancels_export_and_loop_mints_nothing():
    m = make(q=10, every=100)
    m.pulse_export(25)
    m.pulse_import(30)
    m.pulse_export(30)
    assert m.tokens == 2       # max net is 25
    m.pulse_export(5)
    assert m.tokens == 3       # net 30


def test_power_cut_keeps_counters_and_sequence():
    m = make(q=10, every=1)
    m.pulse_export(35)
    assert m.seq == 3
    m.power_cycle()
    assert (m.e_exp, m.tokens, m.seq) == (35, 3, 3)
    m.pulse_export(5)
    assert m.records[-1].parsed.seq == 4


def test_unpersisted_pulses_are_lost_but_nothing_is_double_counted():
    m = make(q=10, every=1)
    m.pulse_export(12)
    m.pulse_export(3, persist=False)
    m.power_cycle()
    assert m.e_exp == 12


def test_calibration_survives_power_cut_and_cannot_be_reprovisioned():
    m = make()
    crc = m.cal_crc
    m.power_cycle()
    assert m.locked and m.cal_crc == crc
    m.provision(calibration_image(99, ROLE_GEN, [b"\xFF"]))
    assert m.meter_id == 7 and m.cal_crc == crc


def test_signer_rollback_guard():
    m = make(q=10, every=1)
    m.pulse_export(20)
    assert len(m.records) == 2
    # Roll the FRAM back to a blank state slot: counters restart from zero.
    for a in (0x0000, 0x0040):
        m.fram.write(a, b"\xFF" * 36)
    m.power_cycle()
    m.pulse_export(10)
    assert m.refused == 1 and len(m.records) == 2


def test_signer_signs_with_meter_key():
    m = make(q=10, every=1)
    m.pulse_export(10)
    sr = m.records[0]
    assert crypto.verify("ML-DSA-44", m.signer.pk, sr.record, sr.signature)
    assert len(sr.signature) == 2420


def test_keygen_happens_once():
    s = SignerOracle()
    s.personalize(1, ROLE_GEN)
    with pytest.raises(RuntimeError):
        s.personalize(1, ROLE_GEN)
    assert s.keygens == 1


def test_zeroize_stops_everything():
    m = make(q=10, every=1)
    m.pulse_export(10)
    m.zeroize()
    m.pulse_export(100)
    m.power_cycle()
    m.pulse_export(100)
    # One token record, then the tamper record; nothing after.
    assert [r.parsed.kind for r in m.records] == [KIND_TOKEN, KIND_TAMPER]
    assert m.signer.wiped
    with pytest.raises(RuntimeError):
        m.signer.personalize(7, ROLE_GRID)


def test_energy_meter_counts_watt_hours():
    em = EnergyMeter(3, ROLE_GEN)
    em.step(3600.0, 0.0, 3600)      # 3.6 kWh
    assert em.mint.e_exp == 3600 and em.mint.tokens == 3
    em.step(0.0, 1800.0, 3600)
    assert em.mint.e_imp == 1800


def test_as_built_meter_signs_every_kwh():
    # Default constants are the as-built ones: q = 1000 Wh, a record per token.
    from enerchain.meter import Q_WH, SIGN_EVERY, EnergyMeter
    assert (Q_WH, SIGN_EVERY) == (1000, 1)
    em = EnergyMeter(9, ROLE_GRID)
    em.step(1000.0, 0.0, 3599)          # 999.7 Wh: nothing yet
    assert em.take_records() == []
    em.step(1000.0, 0.0, 1)             # the 1000th Wh: one token, one record
    r = em.take_records()
    assert [x.parsed.tokens for x in r] == [1]
    em.step(2500.0, 0.0, 3600)          # 2.5 kWh more: tokens 2 and 3
    r = em.take_records()
    assert [x.parsed.tokens for x in r] == [2, 3]
    assert [x.parsed.seq for x in r] == [2, 3]
    for x in r:                          # a record is built as its token mints
        p = x.parsed
        assert p.e_exp - p.e_imp == p.tokens * 1000


def test_resend_after_a_quiet_day_repeats_the_last_record():
    m = make(q=10, every=1)
    m.pulse_export(13)
    assert len(m.records) == 1
    m.idle(RESEND_S - 1)
    assert len(m.records) == 1
    m.idle(1)
    assert len(m.records) == 2
    a, b = m.records[0].parsed, m.records[1].parsed
    assert b.seq == a.seq + 1 and (b.e_exp, b.e_imp, b.tokens) == (a.e_exp, a.e_imp, a.tokens)
    assert b.kind == KIND_TOKEN
    assert crypto.verify("ML-DSA-44", m.signer.pk, m.records[1].record, m.records[1].signature)
    m.idle(2 * RESEND_S)
    assert [r.parsed.seq for r in m.records] == [1, 2, 3, 4]
    m.pulse_export(7)                  # a token restarts the clock
    m.idle(RESEND_S - 1)
    assert [r.parsed.seq for r in m.records] == [1, 2, 3, 4, 5]


def test_no_resend_until_a_record_since_power_up():
    m = make(q=10, every=1)
    m.idle(3 * RESEND_S)
    assert m.records == []
    m.pulse_export(10)
    m.power_cycle()
    m.idle(3 * RESEND_S)
    assert len(m.records) == 1


def test_zeroize_signs_one_tamper_record_with_the_tamper_key():
    m = make(q=10, every=1)
    m.pulse_export(14)
    m.zeroize()
    assert len(m.records) == 2
    sr = m.records[1]
    r = sr.parsed
    assert r.kind == KIND_TAMPER and r.seq == 2 and (r.e_exp, r.tokens) == (14, 1)
    assert crypto.verify("ML-DSA-44", m.signer.tamper_pk, sr.record, sr.signature)
    assert not crypto.verify("ML-DSA-44", m.signer.pk, sr.record, sr.signature)
    m.zeroize()
    m.pulse_export(100)
    m.idle(2 * RESEND_S)
    assert len(m.records) == 2


def test_tamper_key_does_not_outlive_the_wipe_session():
    s = SignerOracle(q=10)
    s.personalize(7, ROLE_GRID)
    s.wipe()
    s.boot()                           # power cut before the tamper record
    raw = MeterRecord(7, ROLE_GRID, 1, 10, 0, 1, 0, kind=KIND_TAMPER).pack()
    assert s.sign_tamper(raw) is None


def test_signer_keeps_record_kinds_apart():
    s = SignerOracle(q=10)
    s.personalize(7, ROLE_GRID)
    tamper = MeterRecord(7, ROLE_GRID, 1, 10, 0, 1, 0, kind=KIND_TAMPER).pack()
    token = MeterRecord(7, ROLE_GRID, 1, 10, 0, 1, 0).pack()
    assert s.sign(tamper) is None              # A1 never signs a tamper record
    assert s.sign_tamper(tamper) is None       # A7 only after a wipe
    s.wipe()
    assert s.sign_tamper(token) is None        # A7 never signs a token record
    assert s.sign_tamper(tamper) is not None
    assert s.sign_tamper(MeterRecord(7, ROLE_GRID, 2, 10, 0, 1, 0,
                                     kind=KIND_TAMPER).pack()) is None   # once


def test_zeroize_before_arming_makes_no_tamper_record():
    m = EcMint1(fram=Fram(), signer=SignerOracle())
    m.signer.personalize(1, ROLE_GEN)
    m.zeroize()
    assert m.records == [] and m.signer.wiped


def test_load_meter_counts_consumption_as_tokens():
    em = EnergyMeter(4, ROLE_LOAD)
    em.step(2500.0, 0.0, 3600)         # 2.5 kWh drawn by the house
    r = em.take_records()
    assert [x.parsed.role for x in r] == [ROLE_LOAD, ROLE_LOAD]
    assert em.mint.tokens == 2
    with pytest.raises(ValueError):
        calibration_image(4, 4, [b"\x01"])
