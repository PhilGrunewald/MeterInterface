% Categorisation
% Working document

Reporting of eight main categories
==================================


Query:
``` SQL
SELECT COUNT(*) AS Instances, Categories.category
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    GROUP BY Categories.category
    ORDER BY Instances DESC;
```

category       	 Instances
--------------   ------
food           	 2208
care_self      	 1427
recreation     	 1409
care_house     	 597
work           	 573
other_category 	 447
care_other     	 438
travel         	 76

Food
====

Query:
The 'a' term returns tuc and number of occurrences in all reported activities.
The 'Join Legend' adds the `meaning` column

``` SQL
SELECT Code, meaning, count FROM
    (SELECT COUNT(*) AS count, Activities.tuc AS Code
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    WHERE Categories.category = 'food'
    GROUP BY Activities.tuc) as a
  JOIN Legend
    ON value = a.Code
    WHERE col = 'tuc'
    ORDER BY count DESC;
```

The results have been regrouped in different ways"

Option 1: By meal phase
-----------------------

Hot drink

count    meaning                 Code
-------  ---------------------   ---
429   	 Hot drink          	 214



Prepare meal

count    meaning                 Code
-------  ---------------------   ---
179   	 Oven               	 8531
157   	 Kettle             	 8535
136   	 Cook on hob        	 8532
67    	 Microwave          	 8533
54    	 Prepare cold meal  	 3111
50    	 Toaster            	 8534
40    	 Lay table          	 3135
28    	 Prepare hot meal   	 3112
28    	 Prepare hot meal   	 3112
5     	 Baking             	 3120
2     	 Getting a takeaway 	 6003
1     	 Toaster            	 3124

Eating

count    meaning                 Code
-------  ---------------------   ---
406   	 Eating hot meal    	 212
173   	 Eating             	 211
95    	 Eat                	 210
95    	 Eat                	 210
79    	 Snack              	 213
8     	 Outdoors eating    	 6001

Generic

count    meaning                 Code
-------  ---------------------   ---
64    	 Food               	 3191
2     	 Food or drink      	 3100
1     	 BBQ                	 6004

After meal

count    meaning                 Code
-------  ---------------------   ---
102   	 Wash dishes        	 3132
73    	 Clear away meal    	 3131
34    	 Dish washer        	 3133
20    	 Dish washing       	 3134
1     	 Lay or clear table 	 3136
2     	 Lay or clear table 	 3130


Option 2 - by energy relation
-----------------------------

Energy intensive
----------------

count    meaning                 Code
-------  ---------------------   ---
429   	 Hot drink          	 214
406   	 Eating hot meal    	 212
179   	 Oven               	 8531
157   	 Kettle             	 8535
136   	 Cook on hob        	 8532
67    	 Microwave          	 8533
50    	 Toaster            	 8534
34    	 Dish washer        	 3133
28    	 Prepare hot meal   	 3112
28    	 Prepare hot meal   	 3112
5     	 Baking             	 3120
1     	 Toaster            	 3124

Not energy intensive
--------------------

count    meaning                 Code
-------  ---------------------   ---
173   	 Eating             	 211
102   	 Wash dishes        	 3132
95    	 Eat                	 210
95    	 Eat                	 210
79    	 Snack              	 213
73    	 Clear away meal    	 3131
64    	 Food               	 3191
54    	 Prepare cold meal  	 3111
40    	 Lay table          	 3135
20    	 Dish washing       	 3134
8     	 Outdoors eating    	 6001
2     	 Food or drink      	 3100
2     	 Getting a takeaway 	 6003
1     	 BBQ                	 6004
1     	 Lay or clear table 	 3136
2     	 Lay or clear table 	 3130

Care self
=========

By phase of day
-------------------------

Bed related

count    meaning                 Code
-------  ---------------------   ---
243   	 Sleep              	 110
155   	 In bed, not asleep 	 111
14    	 Sick in bed        	 120
3     	 Rest or sleep      	 5311

Hygiene 

count    meaning                 Code
-------  ---------------------   ---
212   	 Shower             	 311
147   	 Getting dressed    	 314
54    	 Getting ready      	 302
43    	 Wash               	 313
35    	 Personal care      	 0
26    	 Bathing            	 321
17    	 Hygiene / Beauty   	 315
3     	 Wash and dress     	 310
2     	 Shave              	 8574
14    	 Running a bath     	 320
12    	 Brush teeth        	 8572
6     	 Wash               	 316
5     	 Hair dryer         	 8571
4     	 Do hair            	 8575


Time for oneself

count    meaning                 Code
-------  ---------------------   ---
89    	 Got home           	 304
82    	 Me time            	 303
56    	 Resting            	 5310
79    	 Exercise           	 6100
41    	 Pottering          	 3242
16    	 Exercise           	 9610
16    	 Sport              	 9610
3     	 Me time            	 300

Other

count    meaning                 Code
-------  ---------------------   ---
64    	 Shopping           	 3600
35    	 quick list         	 0
2     	 Work break         	 1120

