-- Fails when Event_ID is missing or reused in the raw input.
SELECT CAST(Event_ID AS STRING) AS Event_ID, COUNT(*) AS row_count
FROM {{ source('careflow_raw', 'hospital_events') }}
GROUP BY CAST(Event_ID AS STRING)
HAVING NULLIF(TRIM(CAST(Event_ID AS STRING)), '') IS NULL OR COUNT(*) > 1
