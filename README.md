**File:** alltrips_canada.dta  
**Purpose:** Dataset of trip-level data for Canadian trips

**Variable Information:**
* **tripid:** Number used to identify each trip
* **route:** Route number (when trip returns multiple routes)
* **mode:** Driving = 0
* **time of day:** Time of query (in hms)
* **day of week:** Monday = 0; Sunday = 6
* **lat_dest:** Latitude of destination
* **lon_dest:** Longitude of destination
* **lat_orig:** Latitude of origin
* **lon_orig:** Longitude of origin
* **pointid_orig:** Point ID of origin
* **citycode:** City code
* **pointid_dest:** Point ID of destination
* **tz:** Local time zone
* **countryname:** Country name
* **cityname_corrected:** City name
* **city_lat:** Latitude of city center
* **city_lon:** Longitude of city center
* **representative_timezone:** Reference time zone (America / Mexico City)
* **diff_real_rep:** Difference between the local time zone and reference time zone
* **time_full_str:** Full day and time of query
* **minofday:** Time of query (minute of day)
* **date:** Date of query
* **trip_dist:** Distance traveled along route (km)
* **traffic_min:** Trip time, real-time traffic (minutes)
* **notraffic_min:** Trip time, no traffic (minutes)
* **usualtraffic_min:** Trip time, 'usual' traffic (minutes)
* **speed:** Overall speed of trip, real-time traffic (km/h)
* **hourofday:** Time of query (hour of day)
* **week:** Week number
* **week_d:** Date of first day in week
* **straightline_dist:** Haversine distance from origin to destination (km)
* **dist_origtocenter:** Distance from trip origin to city center (km)
* **dist_desttocenter:** Distance from trip destination to city center (km)
* **dist_center:** Overall distance of trip to city center (integral measure) (km)
* **type:** 1: radial; 2: circumferential; 3: gravity; 4: places