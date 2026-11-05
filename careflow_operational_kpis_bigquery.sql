-- CareFlow operational KPIs (BigQuery Standard SQL)
-- Replace `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs` with your actual table.
-- Expected columns: case_id, event_id, activity_name, event_timestamp.

-- 1) Patient journey duration per case (first to last event)
WITH case_times AS (
  SELECT case_id,
         MIN(TIMESTAMP(event_timestamp)) AS first_event,
         MAX(TIMESTAMP(event_timestamp)) AS last_event,
         COUNT(*) AS event_count
  FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`
  GROUP BY case_id
)
SELECT COUNT(*) AS total_cases,
       ROUND(AVG(TIMESTAMP_DIFF(last_event, first_event, MINUTE)), 2) AS avg_duration_minutes,
       APPROX_QUANTILES(TIMESTAMP_DIFF(last_event, first_event, MINUTE), 100)[OFFSET(50)] AS median_duration_minutes,
       APPROX_QUANTILES(TIMESTAMP_DIFF(last_event, first_event, MINUTE), 100)[OFFSET(90)] AS p90_duration_minutes,
       MIN(TIMESTAMP_DIFF(last_event, first_event, MINUTE)) AS min_duration_minutes,
       MAX(TIMESTAMP_DIFF(last_event, first_event, MINUTE)) AS max_duration_minutes,
       ROUND(AVG(event_count), 2) AS avg_events_per_case
FROM case_times;

-- 2) Activity volume and case coverage
SELECT LOWER(TRIM(activity_name)) AS activity,
       COUNT(*) AS event_count,
       COUNT(DISTINCT case_id) AS cases_with_activity
FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`
GROUP BY activity ORDER BY event_count DESC;

-- 3) Cases with repeated activities, by activity
WITH per_case_activity AS (
  SELECT case_id, LOWER(TRIM(activity_name)) AS activity, COUNT(*) AS occurrences
  FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`
  GROUP BY case_id, activity
)
SELECT activity,
       COUNTIF(occurrences > 1) AS cases_with_repeat,
       ROUND(100 * SAFE_DIVIDE(COUNTIF(occurrences > 1), (SELECT COUNT(DISTINCT case_id) FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`)), 1) AS pct_all_cases,
       MAX(occurrences) AS max_occurrences_in_one_case
FROM per_case_activity GROUP BY activity ORDER BY cases_with_repeat DESC;

-- 4) Inter-event intervals: use as screening signals, not confirmed queue wait times
WITH ordered AS (
  SELECT case_id, LOWER(TRIM(activity_name)) AS activity,
         TIMESTAMP(event_timestamp) AS event_ts,
         LEAD(LOWER(TRIM(activity_name))) OVER (PARTITION BY case_id ORDER BY TIMESTAMP(event_timestamp), event_id) AS next_activity,
         LEAD(TIMESTAMP(event_timestamp)) OVER (PARTITION BY case_id ORDER BY TIMESTAMP(event_timestamp), event_id) AS next_ts
  FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`
), gaps AS (
  SELECT activity, next_activity,
         TIMESTAMP_DIFF(next_ts, event_ts, MINUTE) AS gap_minutes
  FROM ordered WHERE next_ts IS NOT NULL
)
SELECT activity, next_activity, COUNT(*) AS transition_count,
       APPROX_QUANTILES(gap_minutes, 100)[OFFSET(50)] AS median_gap_minutes,
       APPROX_QUANTILES(gap_minutes, 100)[OFFSET(90)] AS p90_gap_minutes,
       COUNTIF(gap_minutes > 60) AS gaps_over_60_minutes
FROM gaps GROUP BY activity, next_activity
ORDER BY p90_gap_minutes DESC;

-- 5) Start/end pathway validation
WITH ordered AS (
 SELECT case_id, LOWER(TRIM(activity_name)) AS activity,
        ROW_NUMBER() OVER(PARTITION BY case_id ORDER BY TIMESTAMP(event_timestamp), event_id) AS rn_asc,
        ROW_NUMBER() OVER(PARTITION BY case_id ORDER BY TIMESTAMP(event_timestamp) DESC, event_id DESC) AS rn_desc
 FROM `YOUR_PROJECT.YOUR_DATASET.careflow_cleaned_event_logs`
)
SELECT COUNT(DISTINCT case_id) AS total_cases,
       COUNTIF(rn_asc=1 AND activity='registration') AS cases_starting_registration,
       COUNTIF(rn_desc=1 AND activity='discharge') AS cases_ending_discharge
FROM ordered;
