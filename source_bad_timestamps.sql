-- Fails if any source timestamp cannot be parsed as a BigQuery TIMESTAMP.
SELECT Event_ID, Timestamp
FROM {{ source('careflow_raw', 'hospital_events') }}
WHERE Timestamp IS NULL
   OR SAFE_CAST(Timestamp AS TIMESTAMP) IS NULL
