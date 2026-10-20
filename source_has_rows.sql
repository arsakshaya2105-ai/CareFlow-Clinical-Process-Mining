-- Fails when the configured raw table is empty.
SELECT 'careflow_raw.hospital_events has no rows' AS failure_reason
WHERE (SELECT COUNT(*) FROM {{ source('careflow_raw', 'hospital_events') }}) = 0
