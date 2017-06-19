Key statements
==============


  #new_dates
  add new dates

General
=======
    SHOW tables;
    ALTER TABLE TUS2015 AUTO_INCREMENT = 1;
    # Replicate a table
        SHOW CREATE TABLE El_hour;
        # run on source schema and execute the result on destination schema


Experimantal
============

Recategorisation
================

# count how often categories are reported
SELECT COUNT(*) AS Instances, Categories.category
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    GROUP BY Categories.category
    ORDER BY Instances DESC;

# count how often activities within one category are reported

SELECT Code, meaning, count FROM
    (SELECT COUNT(*) AS count, Activities.tuc AS Code
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    WHERE Categories.category = 'care_self'
    GROUP BY Activities.tuc) as a
  JOIN Legend
    ON value = a.Code
    WHERE col = 'tuc'
    ORDER BY count DESC
    ;


SELECT * from Legend LIMIT 5;


SELECT MAX(Watt) AS mWatt, TIME(dt) AS time
    FROM El_hour
    GROUP BY Meta_idMeta;

    JOIN El_hour AS El_max
    On El_max.Watt = El_hour.Watt

SELECT * FROM Legend 
    JOIN Categories
    ON value = tuc
    WHERE col = 'tuc'
    ORDER BY tuc
    LIMIT 29;

SELECT * FROM Legend WHERE value = 311 Limit 5;
SELECT * FROM Categories Limit 5;
SELECT * FROM Activities Limit 5;
SELECT Count(*),tuc,Meta_idMeta FROM Activities GROUP BY tuc,Meta_idMeta;



UPDATE Meta 
    SET Household_idHousehold = -2
    WHERE idMeta = 3107;

SELECT * FROM Meta WHERE idMeta = 3107;





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


Activities
==========
    SELECT * FROM Meter.Activities; WHERE dt_recorded < '2000-01-01 00:00:00';
    
    UPDATE Activities SET dt_recorded = '2000-01-01 00:00:00' WHERE idActivities < 200;
    UPDATE Activities SET dt_recorded = '2000-01-01 00:00:00' WHERE idActivities = 1688 and dt_recorded < '2000-01-01 00:00:00';
    
    SELECT * FROM Meter.Activities where idActivities > 2816;
    SELECT count(*) FROM Meter.Activities;
    SELECT * FROM Meter.Activities where dt_activity like '%16:00:00';
    SELECT * FROM Meter.Activities where activity like 'Washingmachine';
    
    select count(*) from Activities WHere enjoyment > 0;
    UPDATE Meter.Activities SET activity = 'Washing machine' where activity like 'Laundry machine' AND idActivities >2000;
    
    
    SELECT * FROM Meter.Activities where Meta_idMeta = 3085;
    
    update Activities
    set
    dt_recorded =  DATE_ADD(dt_recorded, INTERVAL 1 HOUR)
    where Meta_idMeta = 3084
    and idActivities >0;
    
    
    SELECT * FROM Meter.Activities WHERE path LIKE '%30011,1100%';
    SELECT DISTINCT(Meta_idMeta) FROM Meter.Activities;
    
    UPDATE Activities SET dt_activity  = SUBTIME(dt_activity, '01:00:00') where idActivities >1340 AND Meta_idMeta = 2303;
    
    update Activities set Meta_idMeta = 3035 Where dt_activity > '2017-01-27' AND Meta_idMeta = 2680 AND idActivities > 5000;
    
    
    SELECT count(*) FROM Meter.Activities where Meta_idMeta > 2696 GROUP BY Meta_idMeta;
    
    
    SELECT distinct(Meta_idMeta) FROM Meter.Activities;
    
    
    select * from (select * from Meta as m inner join Electricity as e on m.idMeta = e.Meta_idMeta and m.DataType = 'E') as e
    inner join (select * from Meta as m inner join Activities as a on m.idMeta = a.Meta_idMeta and m.DataType = 'A') as a
    on e.dt >= a.dt_activity and e.dt < (a.dt_activity + interval 10 minute)
    where a.dt_activity = '2016-03-09 04:00:00'
    limit 7;
    
    SELECT dt,tuc,location,enjoyment,Watt,act.Household_idHousehold
    	FROM (
    		SELECT dt_activity,tuc,location,enjoyment,Household_idHousehold
    		FROM Meta
    		JOIN Activities
    		ON idMeta = Meta_idMeta
            ) as act
            JOIN 
            (		
            SELECT dt,watt,Household_idHousehold
    		FROM Meta
    		JOIN Electricity_1min
    		ON idMeta = Meta_idMeta
            ) as el
            ON el.Household_idHousehold = act.Household_idHousehold
            WHERE dt = dt_activity;
            
    
    SELECT dt,tuc,location,enjoyment,Watt,act.Household_idHousehold
    	FROM (
    		SELECT dt_activity,tuc,location,enjoyment,Household_idHousehold
    		FROM Meta
    		JOIN Activities
    		ON idMeta = Meta_idMeta
            ) as act
            JOIN 
            (		
            SELECT dt,watt,Household_idHousehold
    		FROM Meta
    		JOIN Electricity_1min
    		ON idMeta = Meta_idMeta
            ) as el
            ON el.Household_idHousehold = act.Household_idHousehold
            WHERE dt = dt_activity;
            
    CREATE VIEW hh_act AS
    SELECT dt_activity,tuc,location,enjoyment,Household_idHousehold
    		FROM Meta
    		JOIN Activities
    		ON idMeta = Meta_idMeta;
    
    CREATE VIEW hh_el AS
            SELECT dt,watt,Household_idHousehold
    		FROM Meta
    		JOIN Electricity_1min
    		ON idMeta = Meta_idMeta;
    
    CREATE VIEW hh_act_el AS        
    SELECT dt,tuc,location,enjoyment,Watt,act.Household_idHousehold
    	FROM hh_act as act
        JOIN hh_el as el
            ON el.Household_idHousehold = act.Household_idHousehold
            WHERE dt = dt_activity;    
            
            
    
    #activities and corresponding electricity for the hour
    #ok with join, slow with left join
    SELECT A_ID, A_t, A_M, A_loc, A_a, sum(Watt)
    FROM(
    SELECT A_ID, A_t, A_M, A_loc, A_a, E_idHH, E_t, Watt
    FROM(
    SELECT H.idHousehold as A_H, A.idActivities as A_ID, A.dt_activity as A_t, M.idMeta as A_M, A.location as A_loc, A.activity as A_a
    FROM Household as H
    JOIN Meta as M on H.idHousehold = M.Household_idHousehold
    JOIN Activities as A on A.Meta_idMeta = M.idMeta
    #WHERE H.idHousehold = 8117
    ) as alice
    JOIN
    (
    SELECT idHousehold as E_idHH, dt as E_t, Watt
    FROM Electricity_10min as E
    JOIN Meta as M on E.Meta_idMeta = M.idMeta
    JOIN Household as H on H.idHousehold = M.Household_idHousehold
    #WHERE H.idHousehold = 8117
    ) as bob
    on (TIMESTAMPDIFF(MINUTE, E_t, A_t) <= 0 AND TIMESTAMPDIFF(MINUTE, E_t, A_t) >= -60)
    ) as zena
    GROUP BY A_ID;
    
    
    SELECT * FROM hh_el_act_hour
    	JOIN Categories
    	ON Categories.tuc = hh_el_act_hour.tuc;
    
    
    SELECT meaning AS x,
    	   Watt AS y,
    	   dt AS label
    	FROM hh_el_act_hour 
    	JOIN Legend 
    	ON Legend.value = hh_el_act_hour.location
    	WHERE Legend.col = 'location';
    


dates  #new_dates
=====

    #Set new dates
    SELECT * FROM dates WHERE (trialdate >= CURDATE());
    SELECT SUM(places) FROM dates WHERE (trialdate >= CURDATE());
    SELECT * FROM dates WHERE (trialdate >= '2017-08-27');
    xDelete from dates where iddates > 194;
    insert into dates (trialdate,places) VALUES('2017-08-28'+INTERVAL 3 WEEK, 3); # Monday
    insert into dates (trialdate,places) VALUES('2017-08-29'+INTERVAL 3 WEEK, 2); # Tuesday
    insert into dates (trialdate,places) VALUES('2017-08-30'+INTERVAL 3 WEEK, 3);
    insert into dates (trialdate,places) VALUES('2017-08-31'+INTERVAL 3 WEEK, 2);
    insert into dates (trialdate,places) VALUES('2017-09-01'+INTERVAL 3 WEEK, 3); # Friday






    SELECT * FROM Meter.dates;
    
    update trialdate set bookings = 1 where iddata = 31;
    
    SELECT trialdate FROM dates WHERE (trialdate >= CURDATE()+INTERVAL 2 WEEK);
    
    SELECT * FROM dates WHERE (trialdate >= CURDATE());
    
    
    insert into dates (trialdate,places) VALUES('2017-05-08'+INTERVAL 7 WEEK, 3);
    SELECT * FROM dates WHERE (trialdate >= '2017-05-12' + INTERVAL 1 WEEK);
    
    SELECT trialdate FROM (SELECT trialdate, c, bookings
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
    
    
    
    SELECT trialdate
    	FROM dates
        WHERE trialdate NOT IN (SELECT date_choice FROM dateSelection)
        AND (trialdate >= CURDATE()-INTERVAL 2 WEEK);
    
    SELECT date_choice FROM dateSelection;
    
        SELECT 
            `Household`.`date_choice` AS `date_choice`, COUNT(0) AS `c`
        FROM
            `Household`
        GROUP BY `Household`.`date_choice`;
        

Electricity
===========

    Select * FROM Electricity where Meta_idMeta = 1075;
    Select count(idElectricity) FROM Electricity;
    SELECT * FROM Electricity ORDER BY idElectricity DESC LIMIT 1050;
    
    
    LOAD DATA INFILE '/home/phil/meter/null_1040_1.csv' INTO TABLE Electricity FIELDS TERMINATED BY ',' (dt,Watt) SET Meta_idMeta = 9998;
    
    SELECT * FROM Electricity where dt like '2016-07-28 18:05:01' AND Meta_idMeta = 2403;
    SELECT * FROM Electricity where Watt > 4000;
    
    
    select watt FROM Electricity where Meta_idMeta = 2325 and idElectricity % 10 = 0 order by watt;
    
    UPDATE Electricity SET Meta_idMeta = (Meta_idMeta - 372000) WHERE Meta_idMeta >374000 AND idElectricity > 1;
    UPDATE Electricity SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idElectricity > 1;
    
    
    
    SELECT distinct(Meta_idMeta) FROM Meter.Electricity where Meta_idMeta > 1080;


Meta
====

    SELECT * FROM Meter.Meta; 
    
    UPDATE Meta 
      #  SET Household_idHousehold = 1
        WHERE idMeta = 2880;
    
    
    SELECT * FROM Meter.Meta where idMeta = 2621;
    DELETE FROM Meter.Meta where idMeta = 3092;
     
    SELECT * FROM Meter.Meta WHERE Household_idHousehold = 53;
    
    SELECT * FROM Meta WHERE SerialNumber <1000;
    SELECT MAX(SerialNumber)+1 AS sn FROM Meta WHERE SerialNumber <1000;
    SELECT idMeta, dataType, Household_idHousehold, COUNT(*) c FROM Meta WHERE dataType = 'E' GROUP BY Household_idHousehold HAVING c > 1;
    
    # Get households that have repeatedly taken partial
    # >> WEED THEM OUT by creating new HH ids
    SELECT * FROM Meta WHERE DataType = 'E' AND Household_idHousehold IN (
    SELECT Household_idHousehold FROM Meta WHERE DataType = 'E' group by Household_idHousehold having count(Household_idHousehold) >= 2);
    
    
    SELECT * FROM Meter.Meta where Household_idHousehold = 1 AND DataType = 'E' and idMeta >2895;
    UPDATE Household SET status =4 where idHousehold = 1;
    DELETE FROM Meta where Household_idHousehold = 1 AND DataType = 'E' and idMeta >2895;
    
    
    SELECT * FROM Meter.Meta where idMeta > 2696 and DataType = 'A';
    
    SELECT * FROM Meter.Meta where DataType = 'P';
    
    
     WHERE CollectionDate IS NULL;
    SELECT CollectionDate FROM Meter.Meta WHERE idMeta = 99952;
    SELECT idHousehold FROM Household WHERE Contact_idContact = 520;
    
    SELECT * FROM Meta WHERE Household_idHousehold = '99932' AND DataType = 'E';
    SELECT idMeta FROM Meta WHERE DataType = 'E' AND Household_idHousehold = 99932 ORDER BY idMeta DESC LIMIT 1;
    
    
    UPDATE Meta SET Household_idHousehold = (Household_idHousehold - 92000) WHERE Household_idHousehold > 99000 AND idMeta > 1;
    
    UPDATE Meta SET idMeta = (idMeta - 372000) WHERE idMeta >374000;
    UPDATE Activities SET Meta_idMeta = (Meta_idMeta - 372000) WHERE Meta_idMeta >374000 AND idActivities > 1;
    UPDATE Electricity SET Meta_idMeta = (Meta_idMeta - 372000) WHERE Meta_idMeta >374000 AND idElectricity > 1;
    UPDATE Electricity_periods SET Meta_idMeta = (Meta_idMeta - 372000) WHERE Meta_idMeta >374000 AND idElectricity_periods > 1;
    UPDATE Individual SET Meta_idMeta = (Meta_idMeta - 372000) WHERE Meta_idMeta >374000 AND idIndividual > 1;
    
    
    UPDATE Meta SET idMeta = (idMeta - 98000) WHERE idMeta > 99000;
    UPDATE Activities SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idActivities > 1;
    UPDATE Electricity SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idElectricity > 1;
    UPDATE Electricity_periods SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idElectricity_periods > 1;
    UPDATE Individual SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idIndividual > 1;
    
    
    SELECT idMeta FROM Meta WHERE Household_idHousehold = 75 AND DataType = 'A';
    
    
    
    SELECT idMeta FROM Meter.Meta where Household_idHousehold = 1084; 
    
    
    SELECT Meta.idMeta, Household.Contact_idContact, Household.idHousehold
                From Meta
                Join Household 
                On Household.idHOusehold = Meta.Household_idHousehold
                where Household.status >5 AND Household.status < 10 and DataType = 'E';
                
    
    SELECT idMeta FROM Meter.Meta where Household_idHousehold > 8000 and DataType = 'E';
    
    SELECT * FROM Meta WHERE DataType = 'A' ORDER BY RAND() LIMIT 1;
    
    
    
    ALTER TABLE Meta
    ADD uploaded DATETIME DEFAULT NULL;
    

Household
=========

    SELECT * FROM Meter.Household;
    SELECT * FROM Meter.Household where date_choice = '2017-02-06';
    SELECT * FROM Meter.Household where page_number <2;
    SELECT idHousehold, quality FROM Meter.Household where quality = 0;
    SELECT idHousehold,Contact_idContact,status,date_choice FROM Meter.Household where idHousehold = 8117;
    SELECT idHousehold,Contact_idContact,status,date_choice FROM Meter.Household where Contact_idContact = 5529;
    SELECT * FROM Meter.Household where Contact_idContact = 5600;
    SELECT * FROM Meter.Household where idHousehold = 8;
    
    UPDATE Household SET status =4 where idHousehold = 1;
    DELETE FROM Meta where Household_idHousehold = 1 AND DataType = 'E' and idMeta >2895;
    
    
    UPDATE Household SET `quality`= 99 WHERE idHousehold ='8114';
    
    SELECT Contact_idContact,page_number, status FROM Meter.Household where Contact_idContact <2500 AND Contact_idContact >1999;
    
    SELECT * FROM Meter.Household where status < 2 and page_number > 0;
    
    SELECT * FROM Meter.Household where status > 0;
    
    SELECT * FROM Meter.Household where date_choice > "0010-01-01" and date_choice < "2016-01-02";
    SELECT * FROM Meter.Household where date_choice = "2016-01-01";
    
    SELECT * FROM Meter.Household;
    SELECT idHousehold,status,date_choice FROM Meter.Household where Contact_idContact = 5207;
    
    SELECT * FROM Meter.Household where status = 1 and date_choice > '2005-01-01';
    
    UPDATE Meter.Household SET status = 1 where page_number > 17 and status = 0 and idHousehold > 5000;
    
    
    SELECT idMeta FROM Meta WHERE Household_idHousehold = '7971' AND
       DataType = 'A';
       
       
    SELECT Meta.idMeta AS YYY, Household.Contact_idContact AS XXX
    From Meta
    Join Household
    On Household.idHOusehold = Meta.Household_idHousehold
    where Household.Contact_idContact > 500 AND Household.Contact_idContact < 550 AND Meta.DataType = 'E';
    
    SELECT Contact.Name, Contact.email
    	From Contact
        Join Household
        ON Household.Contact_idContact = Contact.idContact
        WHERE Household.status < 2;
    
    
    SELECT Contact.phone
    	From Contact
        Join Household
        ON Household.Contact_idContact = Contact.idContact
        WHERE Contact.idContact = 514
        LIMIT 1;
        
    
    SELECT Meta.idMeta, Household.Contact_idContact, Meta.CollectionDate
                From Meta 
                Join Household 
                On Household.idHOusehold = Meta.Household_idHousehold 
                where Household.Contact_idContact > 507 AND Household.Contact_idContact < 550 AND Meta.DataType = 'E' AND Meta.idMeta > 1073;
                
    SELECT idHousehold FROM Meter.Household where Contact_idContact > 500 AND Contact_idContact < 550;
    
    
    SELECT * FROM Household WHERE (date_choice >= CURDATE());
    
    
    UPDATE Household SET status = '2' WHERE (date_choice >= CURDATE()) AND status < 2 AND idHousehold >0;
    
    select date_choice, count(*) as c FROM Meter.Household GROUP BY date_choice; 
    


Individual
==========

    SELECT * FROM Meter.Individual
    join Meta
    on idMeta=Meta_idMeta;
    
    SELECT * FROM Meter.Individual where Meta_idMeta = 2318;
    
    UPDATE Individual SET `WorkRegularity`='2' WHERE idIndividual = '1003';
    
    UPDATE Individual SET Meta_idMeta = (Meta_idMeta - 98000) WHERE Meta_idMeta >99000 AND idIndividual > 1;
    
    select Meta_idMeta,count(Meta_idMeta) from Individual Group by Meta_idMeta;


Contact
=======
    select * from Contact;
    select * from Contact where idContact = 999;
    select * from Contact where status = 'test';
    
    select * from Contact where (status <> "unsubscribed" OR status IS NULL) AND email like '%@%';
    select * from Contact Where email like '%@%';
    
    ### find duplicates
    SELECT * FROM Contact group by email having count(*) >= 2;
    
    ### GET HH info for Contact ID
    SELECT Contact.email,Contact.status,Household.status, date_choice FROM Household
      JOIN Contact
      ON Household.Contact_idContact = Contact.idContact
      WHERE Household.status >= 3 AND email like '%@%' AND (Contact.status <> "unsubscribed" OR Contact.status IS NULL);

    ### Capitalise
    UPDATE Contact
    SET Name = CONCAT(UCASE(LEFT(Name, 1)),SUBSTRING(Name, 2)),
    	Surname = CONCAT(UCASE(LEFT(Surname, 1)),SUBSTRING(Surname, 2)),
        Address1 = CONCAT(UCASE(LEFT(Address1, 1)), SUBSTRING(Address1, 2)),
        Address2 = CONCAT(UCASE(LEFT(Address2, 1)), SUBSTRING(Address2, 2)),
        Town = CONCAT(UCASE(LEFT(Town, 1)), SUBSTRING(Town, 2)),
        Postcode = UCASE(Postcode)
       where idContact = 5367;
    
    SELECT * FROM Household
      JOIN Contact
      ON Household.Contact_idContact = Contact.idContact
      WHERE idHousehold = 8093;
    
    ### GET HH info for Contact ID
    SELECT Household.status, date_choice FROM Household
      JOIN Contact
      ON Household.Contact_idContact = Contact.idContact
      WHERE idContact = 5410;
      
    select count(idContact) from Contact;
    
    
    SELECT email,Postcode FROM Meter.Contact where Postcode LIKE 'OX%';
    
    select * from Contact where idContact = 311;
    
    UPDATE Contact SET status = 'early' where idContact > 2121 and idContact <2143;
    UPDATE Contact SET status = 'trial' where idContact > 0 and idContact <100;
    
    ###     CAPITALISE NAMES and ADDRESSES
    
    UPDATE Contact
    SET Name = CONCAT(UCASE(LEFT(Name, 1)),SUBSTRING(Name, 2)),
    	Surname = CONCAT(UCASE(LEFT(Surname, 1)),SUBSTRING(Surname, 2)),
        Address1 = CONCAT(UCASE(LEFT(Address1, 1)), SUBSTRING(Address1, 2)),
        Address2 = CONCAT(UCASE(LEFT(Address2, 1)), SUBSTRING(Address2, 2)),
        Town = CONCAT(UCASE(LEFT(Town, 1)), SUBSTRING(Town, 2)),
        Postcode = UCASE(Postcode)
       where idContact > 0;
    
    
    ###    find contacts who 
    ###       - only have one associated HH
    ###       - have no date assigned
    
    #SELECT Contact.idContact,Contact.Name,Contact.email, Contact.status AS C_status, Household.status AS H_status, Household.idHousehold AS idHH,Household.security_code AS sc, Household.date_choice, Household.page_number
    
    SELECT * FROM (
    SELECT Contact.idContact
                     From Contact
                     Join Household
                     ON Household.Contact_idContact = Contact.idContact
                     WHERE Household.status = 1 
                     AND email like '%@%' 
                     AND Contact.status IS NULL
                     )
                     as x
                      group by idContact having count(*) = 1;
    
    ###           PURGE CONTACTS WHO DIDN'T do the sign up (like robots)
    # review contacts that did not complete the survey
    # Contact.status was manually changed from NULL for those worth saving (CNTUR/CEGADS did not do the HH survey)
    
    SELECT * FROM Contact
      JOIN Household
      ON Household.Contact_idContact = Contact.idContact
      WHERE page_number = 0 and Contact.status IS NULL;
    
    # Update Contact.status if wanting to save contacts from purging - e.g.
    UPDATE Contact SET status = 'trial' where idContact > 0 and idContact <100;
    
    # Switch to 'unsafe mode'
    SET SQL_SAFE_UPDATES = 0;
    
    # mark Households for deletion
    Update Household
      JOIN Contact
      ON Household.Contact_idContact = Contact.idContact
      SET Household.status = '-1'
      WHERE Household.page_number = 0 AND Contact.status IS NULL;
    
    # mark Contacts for deletion (once HH are deleted the query condition no longer works...)
    Update Contact
      JOIN Household
      ON Household.Contact_idContact = Contact.idContact
      SET Contact.status = '-1'
      WHERE Household.status = -1;
      
    # check deletees
    SELECT * FROM Contact WHERE Contact.status = -1;
    SELECT * FROM Household WHERE Household.status = -1;
      
    # delete Households
    DELETE FROM Household WHERE Household.status = -1;
    
    # delete Contacts
    DELETE FROM Contact WHERE Contact.status = '-1';
    
    # Switch back to 'safe mode'
    SET SQL_SAFE_UPDATES = 1;


Mailinglist
===========
    SELECT * FROM Meter.Mailinglist;
    UPDATE Mailinglist Set idMailinglist = idMailinglist -92 where idMailinglist > 92;
    
    SELECT Name,email FROM Mailinglist WHERE scope = 'test';
    
    DELETE from Mailinglist where idMailinglist > 184 and status = 'test';
    SELECT Name,email 
    
    FROM Mailinglist WHERE scope = 'test';
    
    SELECT Contact.Name, Contact.email, Mailinglist.status
    	From Contact
        Join Mailinglist
        ON Mailinglist.email = Contact.email;
    
    update Mailinglist m
     join Contact c on
        m.email = c.email
    set m.status = 'participant';
    
    SET SQL_SAFE_UPDATES = 0;
    
    SELECT Mailinglist.email, Mailinglist.status FROM Mailinglist
     join Contact c on
        Mailinglist.email = c.email;

Electricity
===========
    SELECT * FROM Meter.Electricity;
    SELECT * FROM Meter.Electricity where dt < '1999-02-12 04:01:04';
    
    select * from (select * from Meta as m inner join Electricity as e on m.idMeta = e.Meta_idMeta and m.DataType = 'E') as e
    inner join (select * from Meta as m inner join Activities as a on m.idMeta = a.Meta_idMeta and m.DataType = 'A') as a
    on e.dt >= a.dt_activity and e.dt < (a.dt_activity + interval 10 minute)
    where a.dt_activity = '2016-03-09 04:00:00'
    limit 7;
    
    
    select * from (select * from Meta as m inner join Electricity_10min as e on m.idMeta = e.Meta_idMeta and m.DataType = 'E') as e
    inner join (select * from Meta as m inner join Activities as a on m.idMeta = a.Meta_idMeta and m.DataType = 'A') as a
    on e.dt >= a.dt_activity and e.dt < (a.dt_activity + interval 10 minute)
    where a.dt_activity = '2016-05-12 04:10:00'
    limit 7;
    
    CREATE table Electricity_1min like Electricity_10min;
    
    SELECT distinct(Meta_idMeta) FROM Meter.Electricity;
    
    Select count(*) from Electricity;

Electricity_10min
=================
    SELECT * FROM Meter.Electricity_10min WHERE Meta_idMeta = 1078;
    SELECT AVG(Watt) FROM Meter.Electricity_10min;
    
    
    SELECT Meta_idMeta,count(*) FROM Meter.Electricity_10min group by Meta_idMeta;
    
    SELECT AVG(Watt) FROM Electricity_10min WHERE Watt > 20;
    
    SELECT MAX(Watt) FROM Meter.Electricity_10min WHERE Watt > 20 group by Meta_idMeta;
    
    SELECT AVG(baseloads) as meanBaseload, meanLoad, AVG(peaks) as meanPeakload FROM (
    SELECT MIN(Watt) as baseloads FROM Meter.Electricity_1min WHERE Watt > 20 group by Meta_idMeta) as a
    JOIN (
    SELECT AVG(Watt) as meanLoad FROM Electricity_1min WHERE Watt > 20) AS b
    JOIN (SELECT MAX(Watt) AS peaks FROM Meter.Electricity_1min WHERE Watt > 20 group by Meta_idMeta) as c;
    
    
    SELECT AVG(baseloads) as meanBaseload, meanLoad, AVG(peaks) as meanPeakload FROM (
    SELECT MIN(Watt) as baseloads FROM Meter.Electricity WHERE Watt > 20 group by Meta_idMeta) as a
    JOIN (
    SELECT AVG(Watt) as meanLoad FROM Electricity WHERE Watt > 20) AS b
    JOIN (SELECT MAX(Watt) AS peaks FROM Meter.Electricity WHERE Watt > 20 group by Meta_idMeta) as c;
    
    
    SELECT * FROM Meter.Electricity_10min WHERE dt LIKE "%17:30%";
    
    SELECT * FROM Meter.Electricity_10min WHERE TIME(dt) between '17:30:00' AND '18:30:00';

Workshop
========
    SELECT Mailinglist.email FROM Meter.Workshop
    join Mailinglist
    on idMailinglist = Mailinglist_idMailinglist;
    
    SELECT * FROM Meter.Workshop
    join Mailinglist
    on idMailinglist = Mailinglist_idMailinglist;
    
    SELECT * FROM Meter.Workshop
    join Mailinglist
    on idMailinglist = Mailinglist_idMailinglist
    where dinner = 'Yes';
    
    SELECT * FROM Meter.Workshop;
    Update Workshop set dinner = 'No' where idWorkshop = 16;
    Update Workshop set dinner = 'Yes' where idWorkshop = 30;

Legend
======
    SELECT * FROM Meter.Legend order by value;
    SELECT * FROM Meter.Legend where col = 'location';
    
    Select * FROM
    (SELECT idHousehold as bob,ROUND
        (
         COUNT(*)/
             (
             SELECT COUNT(*) as count 
             FROM Household
             WHERE True
             )
         *100
         ,1) as percent 
    FROM Household 
    WHERE True
    GROUP BY bob) as ColPercent
    JOIN Legend
    ON bob = Legend.value
    WHERE Legend.`column` = 'idHousehold'
    AND Legend.`table` = 'Household'
    ORDER BY value;
    
            SELECT idHousehold AS meaning, idHousehold AS value, ROUND 
            (
                COUNT(*)/
                    ( 
                    SELECT COUNT(*) as count  
                    FROM Household 
                    WHERE True 
                    ) 
                *100 
                ,1) as percent  
            FROM Household  
            WHERE True 
            GROUP BY idHousehold;
    
    
    Select value,meaning,percent FROM (SELECT quality AS col,ROUND     (      COUNT(*)/          (          SELECT COUNT(*) as count           FROM Household          WHERE True          )      *100      ,1) as percent      FROM Household      WHERE True     GROUP BY col) as ColPercent JOIN Legend     ON col = Legend.`value`     WHERE Legend.`column` = 'quality'     AND Legend.`table` = 'Household';
    
    
    Select value,meaning,percent 
    	FROM (SELECT age_group5 AS col,ROUND     (      
        COUNT(*)/          (          SELECT COUNT(*) as count           
        FROM Household          WHERE True          )      *100      ,1) as percent      
        FROM Household      WHERE True     
        GROUP BY col) as ColPercent 
    	JOIN Legend     ON col = Legend.`value`     
        WHERE Legend.`column` = 'age_group5'     
        AND Legend.`table` = 'Household';
        
        Select value, value as meaning, percent 
    	FROM (SELECT age_group5 AS value,ROUND     (      
        COUNT(*)/          (          SELECT COUNT(*) as count           
        FROM Household          WHERE True          )      *100      ,1) as percent      
        FROM Household      WHERE True     
        GROUP BY value) as ColPercent;
        
OE_mail
=======
    SELECT * FROM Meter.OE_mail;
    SELECT * FROM Meter.OE_mail where confirmed = "" and (status = 1 or status = 2);
    SELECT * FROM Meter.OE_mail where confirmed = "delegated";
    SELECT * FROM Meter.OE_mail where confirmed = "no";
    SELECT * FROM Meter.OE_mail  
     Join OE_list
     On idOE_list = idOE_mail
     where confirmed = "yes";
    
    SELECT * FROM Meter.OE_mail;
    SELECT * FROM Meter.OE_mail where status = 1;
    SELECT * FROM Meter.OE_mail where status = 2;
    
    xDELETE FROM OE_mail WHERE idOE_mail <400;
    
    
    SELECT distinct(Meta_idMeta) as M FROM Electricity_10min as E WHERE Meta_idMeta NOT IN
                (SELECT idMeta as M FROM Meta);

TUC2015
=======
    SELECT * FROM Meter.TUC2015;
    
    SELECT tuc as x,TimeUse,meaning FROM Meter.TUC2015
     Join Legend
     on Legend.value = TUC2015.tuc
     WHERE Legend.col = 'tuc';
     
    # show any tuc that Meter is not covering with our own Legends
    SELECT tuc,TimeUse 
        FROM TUC2015 
        WHERE tuc NOT IN (
            SELECT value 
            FROM Legend 
            WHERE Legend.col = 'tuc'
            );

    # all tuc and how often they were reported in Hour X
    # 5s, 104 rows
    SELECT COUNT(*), TUS2015.tuc FROM Meter.TUS2015  
    	JOIN Categories
        ON Categories.tuc = TUS2015.tuc
        where Hour(dt_activity) = 18
        GROUP BY tuc
        ;

    # TUS2015 category and its count in a given hour
    # 5s, 8 rows
    SELECT COUNT(*), category FROM TUS2015  
	    JOIN Categories
        ON Categories.tuc = TUS2015.tuc
        where Hour(dt_activity) = 18
        GROUP BY category
        ;

    # METER category and its count in a given hour
    # 
    SELECT COUNT(*), Categories.category FROM Activities  
    	join Categories
        ON Categories.tuc = Activities.tuc
        where Hour(dt_activity) = 18
        GROUP BY category
        ;
