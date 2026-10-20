-- Fails if cleaning unexpectedly removes every event.
SELECT 'stg_hospital_events has no rows' AS failure_reason
WHERE (SELECT COUNT(*) FROM {{ ref('stg_hospital_events') }}) = 0
