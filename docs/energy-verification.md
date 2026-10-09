# Energy Verification

## Objective

Enerchain requires a trustworthy method to verify that electrical energy was actually generated and delivered.

The primary challenge is preventing fraudulent energy claims.

---

## Measurement Requirements

Every generation event must include:

- Meter Identity
- Timestamp
- Voltage
- Current
- Power Factor
- Duration
- Generated kWh
- Digital Signature

---

## Hardware Requirements

Enerchain Meters should contain:

- Secure Element
- Unique Hardware Identifier
- Private Cryptographic Key
- Tamper Detection
- Trusted Firmware

---

## Generation Record

{
  "meter_id": "12345",
  "timestamp": "UTC",
  "voltage": 240,
  "current": 40,
  "power_factor": 0.98,
  "duration": 3600,
  "generated_kwh": 9.4,
  "signature": "..."
}

---

## Verification Process

1. Meter records energy generation.
2. Meter signs record.
3. Record is submitted to Enerchain validators.
4. Network validates authenticity.
5. Delivery confirmation is performed.
6. Proof of Generation accepted.
7. Currency issued.

---

## Anti-Fraud Objectives

Prevent:

- Fabricated generation
- Hardware cloning
- Double counting
- Replay attacks
- Circular energy schemes
- Storage manipulation

---

## Open Research Question

How can Enerchain verify energy production while minimizing reliance upon centralized utilities?
