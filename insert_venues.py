import pandas as pd
import mysql.connector

# Read Excel file
df = pd.read_excel("TOPAZ8 Venue Master.xlsx")

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="system",
    password="dbms1234",
    database="issue_log"
)
cursor = conn.cursor()

# Insert data
for _, row in df.iterrows():
    try:
        cursor.execute("""
            INSERT INTO VENUES (VENUE_CODE, VENUE_NAME, REGION, HUB, CITY)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            row['Venue code'],
            row['Venue name'],
            row['Region'],
            row['Hub'],
            row['venue_add3(City)']
        ))
    except Exception as e:
        print(f"❌ Error inserting {row['Venue code']}: {e}")

conn.commit()
cursor.close()
conn.close()

print("✅ VENUES table has been populated successfully!")
