# Marina
# counts number of entries made by users with valid metaIDs ONLY in their first day of experiment
# () AS bob: creates a selection of MetaID, experiment data, by joining two tables: Meta and Household, and picking the experiment date from the Household table
#joins it to the Activities table using the MetaID field, but only to those entries of the Activities table that have the same date as the experiment

SELECT idMeta, experiment_date, day1, count(Activities.idActivities) as day2
FROM (
SELECT idMeta, experiment_date, count(Activities.idActivities) as day1
FROM
( 
SELECT Meta.idMeta, Household.date_choice as experiment_date
FROM Meta, Household
WHERE Meta.Household_idHousehold = Household.idHousehold
AND Meta.Quality = 1 AND Meta.DataType = 'A'
) as bob 
JOIN Activities
ON Meta_idMeta = idMeta
WHERE date(Activities.dt_activity) = date(experiment_date)
AND time(Activities.dt_activity) BETWEEN '17:00:00' and '21:00:00'
        GROUP BY idMeta) as alice
JOIN Activities
ON Meta_idMeta = idMeta
WHERE abs(date(Activities.dt_activity) - experiment_date) = 1 
AND time(Activities.dt_activity) BETWEEN '17:00:00' and '21:00:00'
        GROUP BY idMeta;



SELECT people,ROUND
    (
     COUNT(*)/
         (
         SELECT COUNT(*) as count 
         FROM Household
         WHERE True
         )
     *100
     ,1) as Percent 
FROM Household 
WHERE True
GROUP BY people
JOIN Legend
ON people = Legend.value
WHERE Legend.column = 'people'
AND Legend.table = 'Household';


# Show table info
SHOW Columns FROM Individual;
# OR just the columns
SELECT COLUMN_NAME 
    FROM information_schema.COLUMNS 
    WHERE table_schema = Meter
    AND table_name = Household;
SELECT column_name FROM information_schema.columns WHERE  table_name = 'Household' AND table_schema = 'Meter';
# Replicate a table
    SHOW CREATE TABLE El_hour;
    # run on source schema and execute the result on destination schema

# List all tables
    SHOW TABLES;

# Get HH stats for cockpit
    SELECT COUNT(*) AS ownC 
    DISTINCT own
    FROM Household 
    LIMIT 10;

SELECT COUNT(*) as count 
FROM Household;



SELECT own,ROUND
    (
    COUNT(*)/
        (
        SELECT COUNT(*) as count 
        FROM Household
        )
    *100
    ) as count 
FROM Household 
GROUP BY own 
ORDER BY own;

# Get HH stats for cockpit
    SELECT DISTINCT own
    FROM Household 
    LIMIT 40;

# Get Meta entry
    SELECT * FROM Meta WHERE idMeta > 3076;
    DELETE FROM Meta WHERE idMeta = 3079;


# next
# get the next three available dates
    SELECT trialdate FROM 
        (
         SELECT trialdate, c, bookings
         FROM dates
         JOIN dateSelection
         ON date_choice = trialdate
         WHERE c < places AND (trialdate >= CURDATE()+INTERVAL 2 WEEK)
        UNION
         SELECT trialdate, c, bookings
         FROM dates
         LEFT JOIN dateSelection
         ON date_choice = trialdate
         WHERE date_choice IS NULL
         AND (trialdate >= CURDATE()+INTERVAL 2 WEEK)
        ) as bob
        ORDER BY trialdate LIMIT 3;
