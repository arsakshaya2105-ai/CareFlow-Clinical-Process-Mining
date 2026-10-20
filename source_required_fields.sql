-- Fails when required identifiers/activity values are null or blank.
SELECT Case_ID, Event_ID, Activity_Name
FROM {{ source('careflow_raw', 'hospital_events') }}
WHERE NULLIF(TRIM(CAST(Case_ID AS STRING)), '') IS NULL
   OR NULLIF(TRIM(CAST(Event_ID AS STRING)), '') IS NULL
   OR NULLIF(TRIM(CAST(Activity_Name AS STRING)), '') IS NULL
