# Exemples de KPI calculés
## Temps de travail machine
SELECT SUM(duration_seconds)
FROM events
WHERE machine_id = 1
AND event_type = 'MACHINE_ACTIVE'
AND DATE(event_time) = CURDATE();

## Production journalière
SELECT SUM(quantity)
FROM production_counts
WHERE machine_id = 1
AND DATE(recorded_at) = CURDATE();

## Efficacité
efficacité = (temps actif / temps total) × 100