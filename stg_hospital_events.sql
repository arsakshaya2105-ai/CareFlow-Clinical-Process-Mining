{{ config(materialized='view') }}

-- Type and validate raw events. Preserve the original activity label for auditability.
WITH source_rows AS (
    SELECT
        NULLIF(TRIM(CAST(Case_ID AS STRING)), '') AS case_id,
        NULLIF(TRIM(CAST(Event_ID AS STRING)), '') AS event_id,
        NULLIF(TRIM(CAST(Activity_Name AS STRING)), '') AS activity_name_raw,
        SAFE_CAST(Timestamp AS TIMESTAMP) AS event_timestamp,
        NULLIF(TRIM(CAST(Department AS STRING)), '') AS department,
        NULLIF(TRIM(CAST(Patient_Category AS STRING)), '') AS patient_category,
        NULLIF(TRIM(CAST(Doctor_ID AS STRING)), '') AS doctor_id,
        NULLIF(TRIM(CAST(Activity_Status AS STRING)), '') AS activity_status
    FROM {{ source('careflow_raw', 'hospital_events') }}
),
valid_rows AS (
    SELECT *
    FROM source_rows
    WHERE case_id IS NOT NULL
      AND event_id IS NOT NULL
      AND activity_name_raw IS NOT NULL
      AND event_timestamp IS NOT NULL
),
deduplicated AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY event_id ORDER BY event_timestamp, case_id
    ) AS event_rank
    FROM valid_rows
)
SELECT
    case_id,
    event_id,
    activity_name_raw,
    LOWER(REGEXP_REPLACE(TRIM(REGEXP_REPLACE(activity_name_raw, r'\\s+', ' ')), r'[^a-zA-Z0-9 ]', '')) AS activity_name_normalized,
    event_timestamp,
    DATE(event_timestamp) AS event_date,
    department,
    patient_category,
    doctor_id,
    activity_status
FROM deduplicated
WHERE event_rank = 1
