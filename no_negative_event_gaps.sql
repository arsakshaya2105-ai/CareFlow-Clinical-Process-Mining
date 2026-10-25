-- This test should return zero rows. Negative gaps indicate ordering or timestamp problems.
SELECT case_id, event_id, previous_event_timestamp, event_timestamp, minutes_since_previous_event
FROM {{ ref('int_activity_events') }}
WHERE minutes_since_previous_event < 0
