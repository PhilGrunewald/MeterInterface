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
