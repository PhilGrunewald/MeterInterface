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
----

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

The results have been regrouped in manually as follows:

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

Food

count    meaning                 Code
-------  ---------------------   ---
64    	 Food               	 3191
2     	 Food or drink      	 3100
1     	 BBQ                	 6004

clear meal

count    meaning                 Code
-------  ---------------------   ---
102   	 Wash dishes        	 3132
73    	 Clear away meal    	 3131
34    	 Dish washer        	 3133
20    	 Dish washing       	 3134
1     	 Lay or clear table 	 3136
2     	 Lay or clear table 	 3130

``` SQL
Update Categories
 SET subcategory = 'clear meal'
 WHERE tuc in (3132, 3131, 3133, 3134, 3136, 3130)
 AND tuc >0;
```


Care self
---------

Bed related

``` SQL
Update Categories
 SET subcategory = 'bed'
 WHERE tuc in (110, 111, 120, 5311)
 AND tuc >0;
```
count    meaning                 Code
-------  ---------------------   ---
243   	 Sleep              	 110
155   	 In bed, not asleep 	 111
14    	 Sick in bed        	 120
3     	 Rest or sleep      	 5311

personal

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



Recreation
----------

``` SQL
SELECT Code, meaning, count FROM
    (SELECT COUNT(*) AS count, Activities.tuc AS Code
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    WHERE Categories.category = 'recreation'
    GROUP BY Activities.tuc) as a
  JOIN Legend
    ON value = a.Code
    WHERE col = 'tuc'
    ORDER BY count DESC;
```


Mindful

count 	 meaning                  	 Code
-------  --------------------------  ----
186   	 Reading                  	 8120
186   	 Socialising              	 5190
58    	 Gardening                	 3410
1     	 Toys                     	 8557
9     	 Music                    	 8556

TV

count 	 meaning                  	 Code
-------  --------------------------  ----
368   	 Watching TV              	 8215
97    	 TV                       	 8553
44    	 Screen time              	 8221

Online

count 	 meaning                  	 Code
-------  --------------------------  ----
122   	 Internet                 	 3720
111   	 email                    	 7170
30    	 Social media             	 8001
4     	 Computer games           	 8552

Phone

count 	 meaning                  	 Code
-------  --------------------------  ----
9     	 Phone                    	 8556
3     	 Telephone conversation   	 5140

Travel

count 	 meaning                  	 Code
-------  --------------------------  ----
125   	 Travel (leisure)         	 9600
62    	 Travel (social)          	 9500
2     	 Travel (social)          	 9510
1     	 Travel for entertainment 	 9520


``` SQL
Update Categories
 SET subcategory = 'Mindful'
 WHERE tuc in (8120, 5190, 3410, 8557, 8556 )
 AND tuc >0;

Update Categories
 SET subcategory = 'TV'
 WHERE tuc in (8215, 8553, 8221)
 AND tuc >0;

Update Categories
 SET subcategory = 'Online'
 WHERE tuc in (3720, 7170, 8001, 8552)
 AND tuc >0;

Update Categories
 SET subcategory = 'Phone'
 WHERE tuc in (8556, 5140)
 AND tuc >0;

Update Categories
 SET subcategory = 'Travel'
 WHERE tuc in (9600, 9500, 9510, 9520)
 AND tuc >0;
```




Care_house
---------


``` SQL
SELECT Code, meaning, count FROM
    (SELECT COUNT(*) AS count, Activities.tuc AS Code
    FROM Activities
    JOIN Categories
    ON Categories.tuc = Activities.tuc
    WHERE Categories.category = 'care_house'
    GROUP BY Activities.tuc) as a
  JOIN Legend
    ON value = a.Code
    WHERE col = 'tuc'
    ORDER BY count DESC;
```



Housework

count 	 meaning                  	 Code
-------  --------------------------  ----
95    	 Arrange things          	 3240
33    	 House keeping           	 3200
33    	 Housework               	 3200
28    	 Laundry hanging         	 3313
48    	 Clear up                	 3250
26    	 Cleaning house          	 3211
20    	 Laundry sorting         	 3312
11    	 Cleaning                	 3214
8     	 Looking for things      	 3241
4     	 Clean floors            	 3213
1     	 Laundry                 	 3310
4     	 Laundry                 	 3300

Appliances

count 	 meaning                  	 Code
-------  --------------------------  ----
59    	 Washing machine         	 3311
18    	 Washing machine         	 8541
28    	 Vacuum cleaning         	 3212
19    	 Power tools             	 8515
18    	 Dishwasher              	 8536
18    	 Ironing                 	 3320
6     	 Iron                    	 8545
13    	 Using tumble dryer      	 3314
1     	 Washer-dryer            	 8543
1     	 Tumble dryer            	 8542
3     	 Sewing machine          	 8544
6     	 Household appliance use 	 8510
5     	 Heater                  	 8514
9     	 Online shopping         	 3721
2     	 Garden tools            	 8560

Travel

count 	 meaning                  	 Code
-------  --------------------------  ----
104   	 Household travel        	 9310
104   	 Travel (shop/service)   	 9310
9     	 Going shopping          	 9360

``` SQL
Update Categories
 SET subcategory = 'Housework'
 WHERE tuc in (3240, 3200, 3200, 3313, 3250, 3211, 3312, 3214, 3241, 3213, 3310, 3300)
 AND tuc >0;

Update Categories
 SET subcategory = 'Appliances'
 WHERE tuc in (3311, 8541, 3212, 8515, 8536, 3320, 8545, 3314, 8543, 8542, 8544, 8510, 8514, 3721, 8560)
 AND tuc >0;

Update Categories
 SET subcategory = 'Travel'
 WHERE tuc in (9310,9360)
 AND tuc >0;
 ```


Energy intensity (boolean high/low e_cat)
=========================================


e_cat low
---------


count 	 meaning                  	 Code
-------  --------------------------  ----
243   	 Sleep              	     110
155   	 In bed, not asleep 	     111
14    	 Sick in bed        	     120
3     	 Rest or sleep      	     5311
147   	 Getting dressed    	     314
54    	 Getting ready      	     302
35    	 Personal care      	     0
17    	 Hygiene / Beauty   	     315
2     	 Shave              	     8574
89    	 Got home           	     304
82    	 Me time            	     303
56    	 Resting            	     5310
79    	 Exercise           	     6100
41    	 Pottering          	     3242
16    	 Exercise           	     9610
16    	 Sport              	     9610
3     	 Me time            	     300
64    	 Shopping           	     3600
2     	 Work break         	     1120
12    	 Brush teeth        	     8572
62    	 Travel (social)          	 9500
58    	 Gardening                	 3410
9     	 Music                    	 8556
9     	 Phone                    	 8556
3     	 Telephone conversation   	 5140
2     	 Travel (social)          	 9510
1     	 Toys                     	 8557
1     	 Travel for entertainment 	 9520
186   	 Reading                  	 8120
186   	 Socialising              	 5190
125   	 Travel (leisure)         	 9600
173   	 Eating             	     211
102   	 Wash dishes        	     3132
95    	 Eat                	     210
95    	 Eat                	     210
79    	 Snack              	     213
73    	 Clear away meal    	     3131
64    	 Food               	     3191
54    	 Prepare cold meal  	     3111
40    	 Lay table          	     3135
20    	 Dish washing       	     3134
8     	 Outdoors eating    	     6001
2     	 Food or drink      	     3100
2     	 Getting a takeaway 	     6003
1     	 BBQ                	     6004
1     	 Lay or clear table 	     3136
2     	 Lay or clear table 	     3130


e_cat high
----------


count 	 meaning                  	 Code
-------  --------------------------  ----
212   	 Shower             	     311
43    	 Wash               	     313
26    	 Bathing            	     321
3     	 Wash and dress     	     310
14    	 Running a bath     	     320
6     	 Wash               	     316
5     	 Hair dryer         	     8571
4     	 Do hair            	     8575
368   	 Watching TV              	 8215
122   	 Internet                 	 3720
111   	 email                    	 7170
97    	 TV                       	 8553
44    	 Screen time              	 8221
30    	 Social media             	 8001
4     	 Computer games           	 8552
429   	 Hot drink          	     214
406   	 Eating hot meal    	     212
179   	 Oven               	     8531
157   	 Kettle             	     8535
136   	 Cook on hob        	     8532
67    	 Microwave          	     8533
50    	 Toaster            	     8534
34    	 Dish washer        	     3133
28    	 Prepare hot meal   	     3112
28    	 Prepare hot meal   	     3112
5     	 Baking             	     3120
1     	 Toaster            	     3124


``` SQL
SELECT * FROM Categories
    WHERE e_cat = 'low';

SELECT * FROM Categories
    WHERE e_cat = 'high';

Update Categories
 SET e_cat = 'high'
 WHERE tuc in (214, 212, 8531, 8535, 8532, 8533, 8534, 3133, 3112, 3112, 3120, 3124,110, 111, 120, 5311, 314, 302, 0, 315, 8574, 304, 303, 5310, 6100, 3242, 9610, 9610, 300, 3600, 0, 1120, 8572, 311, 313, 321, 310, 320, 316, 8571, 8575, 8215, 3720, 7170, 8553, 8221, 8001, 8552)
 AND tuc >0;

Update Categories
 SET e_cat = 'low'
 WHERE tuc in (120, 5311, 314, 302, 0, 315, 8574, 304, 303, 5310, 6100, 3242, 9610, 9610, 300, 3600, 1120, 8572, 9500, 3410, 8556, 8556, 514)
 AND tuc >0;
```
