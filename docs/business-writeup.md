# AutoCare Voice Agent — Business Write-Up

**Use case:** Multilingual voice bot for automotive dealership service desks
**Audience:** Dealership Group CTO / VP Customer Operations
**Prepared for:** Sarvam AI Pre-Sales Engineer Assignment

---

## 1. The Problem

Auto dealership service desks in India are drowning in repetitive inbound phone
calls. A typical multi-location dealer group runs contact centers where the majority
of calls are simple, Tier-1 requests:

- *"Meri car ki service book karni hai"* (book a service slot)
- *"Mere model pe koi recall hai kya?"* (recall check)
- *"Apna appointment reschedule karna hai"* (reschedule)
- *"Service ka status kya hai?"* (job status)

The operational pain:

- **Volume & repetition:** 60–70% of inbound calls are the same handful of intents,
  yet each one occupies a trained human agent.
- **Peak-hour abandonment:** mornings and post-weekend spikes cause long hold times;
  abandoned calls are lost service revenue and a CSAT hit.
- **Language friction:** customers speak **Hindi, English, and Hinglish
  interchangeably**. Agents are hired for language coverage, raising cost and
  limiting scale across regions.
- **After-hours gap:** the desk is closed evenings/Sundays — exactly when working
  owners try to call — so bookings leak to walk-ins and competitors.

> **Illustrative scale:** a mid-size dealer group of ~50 service centers averaging
> ~2,000 service-related inbound calls each per month handles **~100,000 calls/month**,
> of which **~65% are automatable Tier-1** interactions.

---

## 2. Why AI (vs. the current approach)

Today these calls are handled by human agents or a rigid touch-tone IVR. Both fail:

- **Human agents** are expensive, don't scale to peaks, and can't cover every
  language/dialect combination 24×7.
- **Touch-tone IVR** ("press 1 for service") is rigid, English/Hindi-menu-bound, and
  notoriously abandoned — it can't understand *"kal subah 10 baje Swift ki service."*

A **conversational voice bot** is a better fit because:

- It **understands natural, code-mixed speech** the way customers actually talk — no
  menu trees.
- It is **available 24×7** and scales elastically to call spikes at near-zero
  marginal cost.
- It **captures structured data** (vehicle, service type, date, intent) and **routes
  only complex/irate calls to humans**, so agents focus on high-value work.

**Who is the end user?** Vehicle owners across metros and Tier-2/3 towns with **mixed
digital literacy**. Many are more comfortable *speaking* in their own language than
navigating an app or web form — which is precisely why a **voice-first, vernacular**
interface wins here.

---

## 3. Why Sarvam

Generic STT/TTS/LLM stacks are built English-first and degrade badly on Indian
languages and code-mixing. Sarvam is purpose-built for exactly this market:

| Capability | Sarvam advantage | Why it matters here |
|------------|------------------|---------------------|
| **Indian-language STT** (Saaras v3) | 11 Indian languages + English, robust to **Hinglish code-mixing** | Correctly transcribes *"morning slot chahiye, not evening"* — where generic STT fails |
| **India-tuned LLM** (sarvam-105b) | Natural Hindi/Hinglish generation with the right register ("ji", "aap") | Responses sound like a local service advisor, not a translated script |
| **Indian-voice TTS** (Bulbul v2) | 37+ natural Indian voices | Callers trust and understand a native-sounding voice, improving completion rates |
| **Data sovereignty** | India-hosted / on-prem options | Meets enterprise compliance for customer PII — a hard requirement for BFSI-adjacent auto finance data |
| **Single vendor, full stack** | STT + LLM + TTS + Translate from one API | Lower integration surface, consistent latency, one commercial relationship |

**Bottom line:** the moat of this solution *is* the India-specific language quality,
and that is Sarvam's core strength versus generic global providers.

---

## 4. Architecture Summary (business view)

A customer calls the dealership's normal phone number. The call is answered by an AI
voice agent that listens, understands, replies in natural Hindi/Hinglish, and books
the appointment — handing off to a human only when needed. Every call is
automatically summarized and logged to a **live dashboard** the service manager
watches in real time.

```
Customer (phone)  ──►  Telephony (Twilio)  ──►  AI Voice Agent (cloud app)
                                                     │
                        ┌────────────────────────────┼────────────────────────────┐
                        ▼                            ▼                             ▼
                Sarvam STT (Saaras v3)      Sarvam LLM (sarvam-105b)      Sarvam TTS (Bulbul v2)
                 speech → text               understand + reply +          text → natural voice
                                             summarize                            │
                        └────────────────────────────┬────────────────────────────┘
                                                     ▼
                                    CRM + Live Manager Dashboard
                                 (customer status, call summaries)
```

*A detailed system diagram with all components and data flows is in
[`architecture.svg`](architecture.svg).*

---

## 5. ROI / Business Case

**Assumptions (illustrative, per the scenario above):**

| Assumption | Value |
|------------|-------|
| Automatable Tier-1 calls / month | 65,000 |
| Fully-loaded human cost per call | ₹35 |
| AI cost per call (Sarvam STT+LLM+TTS + telephony) | ₹5 |
| Automation rate (of Tier-1) | 70% |

**Calculation:**

- Calls automated / month = 65,000 × 70% = **45,500**
- Savings per automated call = ₹35 − ₹5 = **₹30**
- **Monthly savings ≈ 45,500 × ₹30 = ₹13.65 lakh**
- **Annual savings ≈ ₹1.6 crore**

**Beyond direct cost:**

- **Zero abandonment** during peaks and **24×7 after-hours booking** → recovered
  service revenue (typically the larger prize than agent-cost savings).
- **Agents redeployed** to high-value retention, upsell, and complaint resolution.
- **100% call logging + summaries** → analytics on demand patterns, recall
  compliance, and CSAT that a human desk never captures.

> Even at half the assumed automation rate, the solution pays back the integration
> effort within the first quarter.

---

## 6. Limitations & Next Steps

**What this PoC intentionally does *not* yet do (production gaps):**

- **State persistence:** CRM/call records are in-memory (demo). Production needs a
  database + integration with the dealership DMS/CRM (Salesforce, Zoho, Leadsquared).
- **True slot booking:** the bot confirms conversationally; production must write to
  the live service calendar and send a **WhatsApp/SMS confirmation**.
- **Latency:** current STT is a Twilio-first / Sarvam-recording hybrid. Production
  should use **real-time streaming STT/TTS** (Sarvam via LiveKit/Pipecat) for
  sub-second, barge-in-capable conversations.

**90-day enterprise rollout plan:**

| Phase | Weeks | Deliverable |
|-------|-------|-------------|
| **1. Foundations** | 1–3 | Streaming voice infra (LiveKit + Sarvam), persistent datastore, security/PII review |
| **2. Integration** | 4–7 | DMS/CRM integration, live slot availability, WhatsApp/SMS confirmations |
| **3. Pilot** | 8–10 | Single-region pilot on real traffic, human-in-the-loop warm transfer, QA dashboard |
| **4. Scale** | 11–13 | Multi-language expansion, post-call analytics pipeline, rollout to all centers |

**Success metrics:** % Tier-1 automated, average handle time, call abandonment rate,
booking conversion, CSAT, and cost-per-call — reviewed against the ROI model above.

---

*Solution demo, code, and full technical README:
[github.com/suddh123-ship-it/sarvam](https://github.com/suddh123-ship-it/sarvam)*
