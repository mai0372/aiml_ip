# Indian Residential Tenancy Law Sources & Verification Guide

> **Notice**: Rules in ClauseLens are based on Indian statutory principles and model frameworks as summarized. Applicability varies significantly by state jurisdiction and local municipal enactments. This platform does not provide legal advice.

---

## 1. Statutory Seed Rules Overview

| Rule ID | Title | Governing Statute | Section / Provision | Official Source Link | Applicability | Default Review Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R01** | Security Deposit Cap | Model Tenancy Act, 2021 | Chapter V, Section 11(1) | [Ministry of Housing and Urban Affairs (MoHUA)](https://mohua.gov.in/upload/uploadfiles/files/Model_Tenancy_Act_English.pdf) | Model law, state adoption varies | `reviewed: false` |
| **R02** | Prior Written Notice for Landlord Entry | Model Tenancy Act, 2021 | Chapter IV, Section 15(1) | [MoHUA Model Tenancy Act](https://mohua.gov.in/upload/uploadfiles/files/Model_Tenancy_Act_English.pdf) | Model law, state adoption varies | `reviewed: false` |
| **R03** | Rent Revision Notice Period | Model Tenancy Act, 2021 | Chapter III, Section 9(1) | [MoHUA Model Tenancy Act](https://mohua.gov.in/upload/uploadfiles/files/Model_Tenancy_Act_English.pdf) | Model law, state adoption varies | `reviewed: false` |
| **R04** | Prohibition on Severing Essential Services | Model Tenancy Act, 2021 | Chapter IV, Section 20(1) | [MoHUA Model Tenancy Act](https://mohua.gov.in/upload/uploadfiles/files/Model_Tenancy_Act_English.pdf) | Model law, state adoption varies | `reviewed: false` |
| **R05** | Excessive Penalty or Forfeiture | Indian Contract Act, 1872 | Section 74 | [India Code - Indian Contract Act 1872](https://www.indiacode.nic.in/handle/123456789/2187) | Central Act | `reviewed: false` |
| **R06** | Asymmetric Notice Periods | Indian Contract Act & General Principles | Sections 14, 23 | [India Code - Indian Contract Act 1872](https://www.indiacode.nic.in/handle/123456789/2187) | Central Act / Equity Doctrine | `reviewed: false` |
| **R07** | Term > 11 Months Without Registration | Registration Act, 1908 | Section 17(1)(d) | [India Code - Registration Act 1908](https://www.indiacode.nic.in/handle/123456789/2347) | Central Act | `reviewed: false` |
| **R08** | Notice Period Shorter Than Statutory Default | Transfer of Property Act, 1882 | Section 106 | [India Code - Transfer of Property Act 1882](https://www.indiacode.nic.in/handle/123456789/2338) | Central Act (subject to local rent control) | `reviewed: false` |
| **R09** | Heavy Lock-in Period Exit Penalty | Indian Contract Act, 1872 | Section 74 (Liquidated Damages vs Penalty) | [India Code - Indian Contract Act 1872](https://www.indiacode.nic.in/handle/123456789/2187) | Central Act | `reviewed: false` |
| **R10** | Missing Essential Tenancy Provisions | Model Tenancy Act / Standard Contract Practice | Closed-world sanity checklist | [MoHUA Model Tenancy Act Guidelines](https://mohua.gov.in/) | Best Practice / Advisory | `reviewed: false` |

---

## 2. State Variation Notes for Model Tenancy Act (MTA) Provisions

The **Model Tenancy Act (MTA), 2021** was circulated by the Union Cabinet for adoption by States and Union Territories. Because land and tenancy fall under State powers in the Indian Constitution (Seventh Schedule, List II, Entry 18):
1. **Andhra Pradesh, Tamil Nadu, Uttar Pradesh, and Assam** have taken steps toward enacting state-specific tenancy frameworks influenced by the MTA.
2. In other states (e.g. Maharashtra governed by the *Maharashtra Rent Control Act, 1999*, Delhi governed by the *Delhi Rent Control Act, 1958*, or West Bengal), traditional rent control legislation and the *Transfer of Property Act, 1882* remain the binding primary statutes.
3. Therefore, all MTA-derived rules (R01, R02, R03, R04) in ClauseLens explicitly bear the qualifier:
   `"Model law or general principle; applicability depends on state legislative adoption. Check your state's Tenancy Act."`

---

## 3. Legal Verifier Checklist for Human Counsel

When a legal researcher or attorney reviews and certifies rules in `backend/app/kb/rules/in_residential_generic.yaml`, follow this checklist:

- [ ] **Check 1: Official Portal Link**: Verify the link directs to `indiacode.nic.in`, `mohua.gov.in`, or a certified state gazette.
- [ ] **Check 2: Exact Verbatim Section Text**: Paste the exact text from the official Gazette into `source_text`. Do not summarize in the source text field.
- [ ] **Check 3: Judicial Precedents**: Note whether any landmark Supreme Court or High Court judgment impacts the section (e.g. *Kailash Nath Associates v. DDA* for s. 74 penalty vs reasonable compensation).
- [ ] **Check 4: State Overrides**: Document state amendments (e.g. state-specific stamp duty or registration exemptions).
- [ ] **Check 5: Update Metadata**: Set `reviewed: true`, record `reviewed_by: "Advocate <Name>"`, and record the current date in `reviewed_on: "YYYY-MM-DD"`.

