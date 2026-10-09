"""EC-MINT1 / QS7001 reference model: the rules the hardware enforces."""

import pytest

from enerchain import crypto
from enerchain.meter import EcMint1, EnergyMeter, Fram, SignerOracle, calibration_image
from enerchain.record import ROLE_GEN, ROLE_GRID, MeterRecord, RecordError, crc8, crc16


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
        MeterRecord(1, 1, 1, 1 << 48, 0, 0, 0).pack()


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
    assert len(m.records) == 1 and m.signer.wiped
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
