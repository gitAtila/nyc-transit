from sys import argv
import csv
import pandas as pd

taxi_data_path = argv[1]
with open (taxi_data_path, 'rb') as csv_file:
    csv_reader = csv.reader(csv_file)

    csv_headings = next(csv_reader)

    # vendor_name,
    # Trip_Pickup_DateTime,
    # Trip_Dropoff_DateTime,
    # Passenger_Count,
    # Trip_Distance,
    # Start_Lon,
    # Start_Lat,
    # Rate_Code,
    # store_and_forward,
    # End_Lon,
    # End_Lat,
    # Payment_Type,
    # Fare_Amt,
    # surcharge,
    # mta_tax,
    # Tip_Amt,
    # Tolls_Amt,
    # Total_Amt

    print csv_headings

    for row in csv_reader:
		print row

        break
