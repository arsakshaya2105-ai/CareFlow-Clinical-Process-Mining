{{ config(materialized='view') }}

-- Standardize the raw CareFlow event log before process-mining analysis.
-- Keep the source fields recognizable so dashboard and PM4Py steps can reuse them.
WITH typed_events AS (
    SELECT
        NULLIF(TRIM(CAST(Case_ID AS STRING)), '') AS Case_ID,
        NULLIF(TRIM(CAST(Event_ID AS STRING)), '') AS Event_ID,
        NULLIF(TRIM(CAST(Activity_Name AS STRING)), '') AS Activity_Name,
        SAFE_CAST(Timestamp AS TIMESTAMP) AS event_timestamp,
        NULLIF(TRIM(CAST(Department AS STRING)), '') AS Department,
        NULLIF(TRIM(CAST(Patient_Category AS STRING)), '') AS Patient_Category,
        NULLIF(TRIM(CAST(Doctor_ID AS STRING)), '') AS Doctor_ID,
        NULLIF(TRIM(CAST(Activity_Status AS STRING)), '') AS Activity_Status
    FROM {{ source('careflow_raw', 'hospital_events') }}
),
valid_events AS (
    SELECT *
    FROM typed_events
    WHERE Case_ID IS NOT NULL
      AND Event_ID IS NOT NULL
      AND Activity_Name IS NOT NULL
      AND event_timestamp IS NOT NULL
),
ranked_events AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY Event_ID ORDER BY event_timestamp, Case_ID
    ) AS event_row_number
    FROM valid_events
)
SELECT
    Case_ID, Event_ID, Activity_Name, event_timestamp,
    Department, Patient_Category, Doctor_ID, Activity_Status
FROM ranked_events
WHERE event_row_number = 1
