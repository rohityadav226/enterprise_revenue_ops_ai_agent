---
document_id: NXF-SALES-POL-001
title: Sales Operating Policy
document_type: sales_policy
version: "1.0"
effective_date: 2026-01-01
owner: Revenue Operations
classification: internal
allowed_roles:
  - sales_rep
  - sales_manager
  - sales_leader
  - revops_analyst
  - admin
tags:
  - opportunity-management
  - sales-process
  - pipeline-definitions
  - crm-hygiene
---

# Sales Operating Policy

## 1. Purpose and scope

This policy describes the standard operating rules for managing sales opportunities in the fictional NexusFlow sales organization. It applies to sales representatives, sales managers, sales leaders, and Revenue Operations personnel who create, update, review, or report on opportunities.

This document is a synthetic training policy. It does not replace an executed customer contract or an approved production policy.

## 2. Opportunity stage definitions

NexusFlow uses the following opportunity stages:

| Stage | Open or closed | Definition | Minimum evidence to enter or exit |
|---|---|---|---|
| Qualification | Open | A potential customer and a plausible business need have been identified. | Record the business problem, initial fit, contact, estimated value, owner, and expected close date. |
| Discovery | Open | The sales representative is validating requirements, stakeholders, impact, and decision process. | Record discovery findings, success criteria, key stakeholders, and next customer action. |
| Proposal | Open | A solution and commercial proposal have been presented or formally prepared for the customer. | Attach or reference the proposal, document scope and pricing assumptions, and record the customer's response or next review date. |
| Negotiation | Open | The customer is reviewing commercial or contractual terms and the parties are working toward a decision. | Record open commercial issues, approval status, decision owner, and target decision date. |
| Closed Won | Closed | The customer has signed or otherwise completed the required contract process. | Record the closed date and ensure the corresponding booking record is created through the approved booking process. |
| Closed Lost | Closed | The opportunity will not proceed. | Record the closed date and a standardized loss reason. |

The four open stages are **Qualification, Discovery, Proposal, and Negotiation**. Closed Won and Closed Lost are not part of open pipeline.

## 3. Opportunity data requirements

Every active opportunity must have:

- A named opportunity owner.
- A linked account and a primary customer contact where available.
- A current stage supported by recorded evidence.
- An expected close date that reflects the current customer decision process.
- Line items with quantity and agreed unit price when a value is being forecast.
- A documented next step and next-step date.
- Recent customer or internal activity recorded in the CRM.

The opportunity owner is responsible for keeping these fields accurate. Managers are responsible for reviewing stale, incomplete, or unsupported opportunities.

## 4. Opportunity value and pipeline definitions

Opportunity value is calculated from its line items:

**Opportunity value = sum of quantity multiplied by agreed unit price for each line item.**

Open pipeline includes opportunities in Qualification, Discovery, Proposal, and Negotiation. It excludes Closed Won and Closed Lost opportunities.

Weighted pipeline is calculated as:

**Weighted pipeline = opportunity value multiplied by the stored opportunity probability divided by 100.**

The probability used in this calculation is the probability stored on the opportunity record. An analyst or AI assistant must not silently substitute a probability based on stage or an undocumented assumption.

Average opportunity value for an open-pipeline report is the arithmetic average of the included open opportunity values. If there are no included opportunities, the system should distinguish an empty result from a failed query.

## 5. Pipeline, bookings, and revenue are different measures

Open pipeline is the value of active opportunities. It is not a booking and is not recognized accounting revenue.

A booking represents the signed contract value recorded in the approved bookings data. Booking reports use the booking record's `booked_at` date for period selection.

For quota attribution, the opportunity owner is the sales attribution owner. The person who records a booking is an operational recorder and must not automatically be treated as the quota owner.

Do not describe pipeline as actual bookings, cash collected, or recognized revenue. Do not combine amounts in different currencies unless an approved foreign-exchange conversion process has been applied and disclosed.

## 6. CRM hygiene and review

Sales representatives should update material opportunity changes within two business days. Material changes include stage movement, expected close date changes, value changes, stakeholder changes, and a confirmed customer decision.

Sales managers should review open pipeline at least weekly. Reviews should focus on evidence, next steps, forecast assumptions, close-date quality, and unresolved risks.

A missing value, date, activity, or source record must not be silently interpreted as zero or as confirmation that no business activity occurred. Report missing information explicitly.

## 7. Exceptions and approvals

Exceptions to the standard sales process must be documented in the CRM and approved by the relevant sales manager or authorized business owner. Commercial discount approvals are governed separately by the Pricing and Discount Policy.
