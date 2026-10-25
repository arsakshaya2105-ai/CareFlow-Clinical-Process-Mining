{{ config(materialized='view') }}

-- Canonicalize common activity variants while retaining normalized source label.
WITH normalized AS (
    SELECT
        *,
        REGEXP_REPLACE(LOWER(TRIM(activity_name_normalized)), r'\\s+', ' ') AS activity_key
    FROM {{ ref('stg_hospital_events') }}
),
canonicalized AS (
    SELECT
        case_id,
        event_id,
        activity_name_raw,
        activity_name_normalized,
        CASE
            WHEN activity_key IN ('registration', 'register', 'patient registration', 'check in', 'check-in') THEN 'Registration'
            WHEN activity_key IN ('triage', 'triaging') THEN 'Triage'
            WHEN activity_key IN ('consultation', 'consult', 'doctor consultation', 'physician consultation') THEN 'Consultation'
            WHEN activity_key IN ('lab test', 'laboratory test', 'laboratory', 'lab') THEN 'Lab Test'
            WHEN activity_key IN ('x ray', 'xray', 'x-ray', 'radiology') THEN 'X-Ray'
            WHEN activity_key IN ('treatment', 'procedure', 'medication') THEN 'Treatment'
            WHEN activity_key IN ('discharge', 'patient discharge', 'checkout', 'check out') THEN 'Discharge'
            ELSE INITCAP(activity_key)
        END AS activity_name,
        event_timestamp,
        event_date,
        department,
        patient_category,
        doctor_id,
        activity_status,
        LAG(event_timestamp) OVER (
            PARTITION BY case_id ORDER BY event_timestamp, event_id
        ) AS previous_event_timestamp,
        TIMESTAMP_DIFF(
            event_timestamp,
            LAG(event_timestamp) OVER (
                PARTITION BY case_id ORDER BY event_timestamp, event_id
            ),
            MINUTE
        ) AS minutes_since_previous_event
    FROM normalized
)
SELECT * FROM canonicalized
