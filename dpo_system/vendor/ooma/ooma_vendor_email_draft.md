Subject: Request to Confirm CSV Import and Disposition Export for DPO Outbound Pilot

Hello Ooma team,

We are preparing a controlled outbound pilot and need written confirmation of the CSV import and disposition export capabilities that apply to your dialer.

To avoid assumptions, we are not presenting the attached file as an Ooma-approved contract. It is the provider-ready outbound format produced by our internal system and aligned to common dialer ingestion patterns, pending your confirmation.

Our operating model is:

1. Produce a batch file from our internal database.
2. Upload a flat CSV to the Ooma dialer.
3. Run outbound activity against that uploaded list.
4. Export dispositions and reconcile them back to our internal workflow and audit system.

Attached are:

1. A 10-row sample CSV representing the provider-ready list we intend to upload.
2. A one-page capability checklist showing the specific questions we need answered before production.

Please confirm the following:

1. Whether the attached CSV shape can be ingested as-is.
2. Which columns are required, optional, ignored, or unsupported.
3. Whether phone numbers must be supplied in strict E.164 format.
4. Whether our row identifier can be preserved and returned in disposition exports.
5. Whether custom fields can be displayed to agents during calling.
6. Whether list- or campaign-level fields can be preserved through reporting.
7. What upload limits, deduplication rules, and export options apply.

We would also like to run a small pilot import using this sample file before preparing a larger production run.

Please return either:

1. A marked-up version of the attached checklist, or
2. Your official import/export specification and any sample templates you require us to follow.

If any attached column names should be changed, removed, or reordered for your ingestion path, please provide the exact expected layout and one accepted sample row.

Thank you,

DPO Team
