# ================================================================================================= #
# Filename  : Tutorial_00_Quixstreams.py
#
# Purpose   : This tutorial introduces the setup of a local Apache Kafka server and the installation
#             of Quix Streams on a Windows-based Python environment, forming the foundation for
#             subsequent hands-on tutorials in Kafka-based stream processing and data engineering.
#
# Remarks   : 1. This file focuses on environment preparation and installation rather than stream
#                processing logic itself.
#             2. The tutorial assumes a Windows 11 system with Conda available for environment
#                management.
#             3. Apache Kafka is configured in KRaft mode, without requiring a separate ZooKeeper
#                installation.
#             4. The instructions include practical adjustments encountered during real setup, such
#                as editing log directories and handling the "wmic" issue.
#             5. This script serves as the prerequisite setup guide for later Quix Streams tutorials
#                involving producers, consumers, transformations, aggregations, and streaming
#                applications.
#
# Composer  : Dr. Hassan Mohy-ud-Din
# Email     : hassan.mohyuddin@lums.edu.pk
# Date      : March 28, 2026
# ================================================================================================= #

# ---------------------------------------------- #
# <<<<<<<<<<<<<<<< Kafka Server >>>>>>>>>>>>>>>> #
# ---------------------------------------------- #

# Installation Instructions
# Reference : https://www.youtube.com/watch?v=OzfvZ0zUnEg&t=607s
# Notes     : I watched the video above before installing it on my Windows 11 system. I had to 
#             make a few tweaks, which I’ve documented below.

# ----- #
# STEP 1
# ----- #

# - Go to https://kafka.apache.org/community/downloads/
# - Scroll down and download Binary downloads: Scala 2.12 - kafka_2.12-3.9.2.tgz file.
# - Extract all its contents, rename it to kafka (keep it simple), and move it to C-drive. 
#   Now, the path of the folder should be "C:\kafka\".

# ----- #
# STEP 2
# ----- #

# Create a conda environment as follows >> conda create --name learn_kafka
# Activate the environment              >> conda activate learn_kafka

# ----- #
# STEP 3
# ----- #

# - Install Java in the environment     >> conda install -c conda-forge openjdk=21 
# - Confirm installation with           >> java -version

# ----- #
# STEP 4
# ----- #

# - Go to "C:\kafka\config\kraft\" and open "server" file in (say) Notepad++.
# - Edit the line "log.dirs= ..." by appending "C:/kafka/" to the "tmp/kraft-combined-logs" 
#	folder. Ultimately, it should read as follows: log.dirs=C:/kafka/tmp/kraft-combined-logs
# - Save the file.

# - Go to "C:\kafka\config\kraft\" and open "reconfig-server" file in (say) Notepad++.
# - Edit the line "log.dirs= ..." by appending "C:/kafka/" to the "tmp/kraft-combined-logs" 
#	folder. Ultimately, it should read as follows: log.dirs=C:/kafka/tmp/kraft-combined-logs
# - Save the file.

# ----- #
# STEP 5
# ----- #

# - Go to "C:\kafka\bin\windows" and open a cmd prompt here and type:
#   >> C:\kafka\bin\windows >> .\kafka-storage.bat random-uuid
#   OR
#   >> C:\kafka\bin\windows >> kafka-storage.bat random-uuid 

#   This generates a UUID, for instance (fictitious), QmR8x2L9Z4T6WpHsCkV3Df

# - Go to "C:\kafka\bin\windows" and open a cmd prompt here and type:
#   >> .\kafka-storage.bat format -t <TYPE UUID HERE> -c C:\kafka\config\kraft\server.properties
#   OR
#   >> kafka-storage.bat format -t QmR8x2L9Z4T6WpHsCkV3Df -c C:\kafka\config\kraft\server.properties

# ----- #
# STEP 6
# ----- #

# - Open a new cmd window and start the Kafka Server using the following commands:
#   >> .\kafka-server-start.bat C:\kafka\config\kraft\server.properties 
#   OR
#   >> kafka-server-start.bat C:\kafka\config\kraft\server.properties 

# - [NOTE] If you encounter a "wmic" error run >> setx KAFKA_HEAP_OPTS "-Xmx1G -Xms1G"
#          and then start the Kafka server using the command above.
# - [VERY IMPORTANT] Do not close this window.



# ---------------------------------------------- #
# <<<<<<<<<<<<<<<< Quix Streams >>>>>>>>>>>>>>>> #
# ---------------------------------------------- #

# Reference : https://quix.io/quix-streams

# ----- #
# STEP 7
# ----- #

# - Make sure you have activated the conda environment >> conda activate learn_kafka
# - Install requests for API calls >> conda install requests
# - Install Quix Streams, open source framework for processing data on Apache Kafka with 
#   Streaming DataFrames. >> python -m pip install quixstreams



# ------------------------------------------ #
# <<<<<<<<<<<<<<<< AIRTABLE >>>>>>>>>>>>>>>> #
# ------------------------------------------ #

# ----- #
# STEP 8
# ----- #

# - Go to https://airtable.com/ and register an account.
# - Login, click your profile icon, and select "Account" i.e., https://airtable.com/account.
# - Scroll down and click "Go to developer hub" under API (probably boxed in yellow). 
#   This will take you to https://airtable.com/create/apikey. 
# - Click "create token". Assign a name, say "Kafka". 

# - Add a scope and select all below:
#
#   data.records:read
#   See the data in records
#
#   data.records:write
#   Create, edit, and delete records
#
#   data.recordComments:read
#   See comments in records
#
#   data.recordComments:write
#   Create, edit, and delete record comments
#
#   schema.bases:read
#   See the structure of a base, like table names or field types
#
#   schema.bases:write
#   Edit the structure of a base, like adding new fields or tables

# - Click "Add all resources" and hit "Create token".
# - A pop window appears, titled "Your token has been created"
#   Copy the token and save it. THIS WILL BE YOUR "API_KEY".
#   You won't be able to see it again. Hit "Done".

# - Go to https://airtable.com/. Click "+" to the right of Workspaces (left panel).
# - Hit "Create a workspace", assign a name (say Kafka), and hit "Buil an app on your own".
# - A new window appears with a url https://airtable.com/app***/tbl***/****blocks=hide
#   Also, a chat window appears on the left-hand-side. 

# - At the very top of the main window panel (not the chat window), rename "Untitled Base"
#   (say Kafka) and hit "Enter key".

# - In the chat window, type the following prompt:
#   Create a spreadsheet titled "HourlyWeatherSummary". The columns of the spreadsheet must 
#   include the following headings: hour_bucket; city; samples_in_hour; avg_temperature_c; 
#   min_temperature_c; max_temperature_c; avg_temperature_f; min_temperature_f; max_temperature_f; 
#   avg_wind_speed; dominant_temperature_band; dominant_wind_direction; summary; 
#   last_observed_time; written_at_unix.

# - Once the prompt executes, it creates a spreadsheet titled "HourlyWeatherSummary" and the 
#   desired schema. You may close the chat panel by hitting "<<".

# - From the url of the window, copy BASE_ID which is "app***". It includes the prefix "app" too.

# - Set environment variables as follows (in the visual studio code terminal)
#   >> $env:AIRTABLE_ACCESS_TOKEN="<API KEY>"
#   >> $env:AIRTABLE_BASE_ID="<BASE ID>"
#   >> $env:AIRTABLE_TABLE_NAME="HourlyWeatherSummary"

# - Run the dummy code on the terminal to confirm everything works
#   >> python dummy.py
# - If it returns some meaningful output, you are good to go. 
#   >> 200
#   >> {'records': [{'id': 'rec1qCWRV8qlfv77I', 'createdTime': '2026-03-28T17:43:14.000Z', 'fields': {}}]}
#   >> TOKEN repr     = '*************************'
#   >> BASE_ID repr   = 'app******'
#   >> TABLE_NAME repr= 'HourlyWeatherSummary'


# ================================================================================================= #
def dummy_code():
    import os, requests
    
    API_KEY         = "********************************************"
    BASE_ID         = "app*********"
    TABLE_NAME      = "HourlyWeatherSummary"

    url             = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

    headers         = {"Authorization": f"Bearer {API_KEY}"}

    response        = requests.get(url, headers = headers)

    print(response.status_code)
    print(response.json())

    print("TOKEN repr     =", repr(os.getenv("AIRTABLE_ACCESS_TOKEN", "")))
    print("BASE_ID repr   =", repr(os.getenv("AIRTABLE_BASE_ID", "")))
    print("TABLE_NAME repr=", repr(os.getenv("AIRTABLE_TABLE_NAME", "")))


# ================================================================================================= #