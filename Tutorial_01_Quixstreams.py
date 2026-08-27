# ================================================================================================= #
# Filename  : Tutorial_01_Quixstreams.py
#
# Purpose   : Demonstrate how to fetch real-time weather data from Open-Meteo and continuously
#             publish it to an Apache Kafka topic using Python and Quixstreams.
#
# Commands  : Follow instructions in Tutorial_00_Quixstreams.py
#
#             Make sure Kafka is running locally (default broker: localhost:9092).
#             In CMD >> kafka-server-start.bat C:\kafka\config\kraft\server.properties
#
#             To run this tutorial, >> python Tutorial_01_Quixstreams.py
#
# Remarks   : 1. This tutorial acts as a Kafka producer.
#             2. It pulls live weather information for Lahore, Pakistan, from the Open-Meteo API.
#             3. Each response is wrapped in a small JSON payload and written to a Kafka topic.
#             4. The code includes basic request validation, logging, and graceful interruption.
#             5. The script is intentionally simple so that it can be used as the first tutorial in
#                a Quixstreams-based Kafka series for Data Engineering.
#
# Reference : https://www.youtube.com/@QuixStreams
#
# Composer  : Dr. Hassan Mohy-ud-Din
# Email     : hassan.mohyuddin@lums.edu.pk
# Date      : March 28, 2026
# ================================================================================================= #

import os, requests, json, logging, time

from quixstreams                        import Application

# ================================================================================================= #
# Global constants used by the tutorial.
DEFAULT_BROKER_ADDRESS              = os.getenv("KAFKA_BROKER", "localhost:9092")                   # if environment variable KAFKA_BROKER exists, otherwise default to "localhost:9092"
LOG_LEVEL                           = "DEBUG"                                                       # desired logging verbosity; DEBUG means the script will print detailed diagnostic information
TOPIC_NAME                          = "weather_data_demo"                                           # Kafka topic to which weather messages will be published
KEY_ID                              = "Salar de Uyuni"      # "Lahore"                              # Kafka message key; often used for partitioning and grouping related messages
CITY_NAME                           = "Salar de Uyuni"      # "Lahore"                              # readable city name inserted into the outgoing payload
LATITUDE                            = -20.1338              # 31.5204
LONGITUDE                           = -67.4891              # 74.3587
POLL_INTERVAL_SECONDS               = 10                                                            # script waits 10 seconds between successive API polls
WEATHER_API_URL                     = "https://api.open-meteo.com/v1/forecast"                      # endpoint for Open-Meteo weather data
REQUEST_TIMEOUT_SECONDS             = 30                                                            # requests raises a timeout-related exception; prevents from hanging indefinitely on a slow network call

# ================================================================================================= #
# Contact Open-Meteo and return the current weather data.
def get_weather():
    """
    Fetch current weather data for Lahore from the Open-Meteo API.
    Returns: dict - Parsed JSON response from the API.
    """
    # HTTP GET request to the Open-Meteo endpoint stored in WEATHER_API_URL.
    response                        = requests.get(WEATHER_API_URL,
                                                   params   = {"latitude"       : LATITUDE,
                                                               "longitude"      : LONGITUDE,
                                                               "current_weather": True,},           # requests current weather data specifically
                                                   timeout=REQUEST_TIMEOUT_SECONDS,)                # sets the maximum wait time for the HTTP request; hen closes the requests.get() call
    
    response.raise_for_status()         # important validation step; raises an exception immediately (e.g., HTTP response code error)
    return response.json()              # parses the HTTP response body as JSON and returns it as a Python dictionary

# ================================================================================================= #
# In the Open-Meteo API, the payload is the set of parameters you send in your request—like latitude, 
# longitude, and current_weather=True—that tells the server what weather data you want.
def build_payload(weather_response):                                                                # takes the raw weather response and wraps it into a cleaner event structure for Kafka
    """
    Wrap the raw API response in a simple event structure that is easier to inspect downstream.
    """
    return {"city"                  : CITY_NAME,
            "latitude"              : LATITUDE,
            "longitude"             : LONGITUDE,
            "source"                : "Open-Meteo",                                                 # records the source system so downstream systems know where the data came from
            "collected_at_unix"     : int(time.time()),                                             # collection time as a Unix timestamp, meaning the number of seconds since January 1, 1970 (called Unix epoch) UTC
            "weather_response"      : weather_response,}                                            # embeds the full raw weather response under a nested key
                                                                                                    # preserves the original API output while stashing it with useful metadata

# ================================================================================================= #
# If a producer is not flushed cleanly, some messages may remain buffered in the producer’s local 
# memory and never actually reach Kafka before the program exits. This can lead to silent message 
# loss, incomplete batches, hidden delivery errors, and uncertainty about which records were truly 
# written. In short, send() often only queues data locally, whereas flush() helps ensure queued 
# and in-flight messages are delivered or fail visibly before shutdown.
def main():
    # Build a Quixstreams application object. Here, we use it only for producer-side interaction.
    app                             = Application(broker_address    = DEFAULT_BROKER_ADDRESS,       # creates a Quixstreams Application instance and configures it to connect to the Kafka broker address
                                                  loglevel          = LOG_LEVEL,)                   # sets the application log level to "DEBUG"

    logging.info("Connecting to Kafka broker at %s"                         , DEFAULT_BROKER_ADDRESS)
    logging.info("Producing weather updates to topic '%s' every %d seconds" , TOPIC_NAME, POLL_INTERVAL_SECONDS)    # logs the topic name and polling interval

    # The producer is a write-only Kafka connection used to publish records to a topic.
    # Producer is the object through which Kafka messages will be sent.
    with app.get_producer() as producer:                                                            # producer is automatically cleaned up when the with block exits
        while True:                                                                                 # script will continue polling and publishing until manually stopped or an unrecoverable failure occurs
            try:
                weather             = get_weather()                                                 # fetch current weather data from Open-Meteo
                payload             = build_payload(weather)                                        # wraps the raw weather response into the custom Kafka event dictionary

                # Logs the full payload at debug level, which is useful for inspection 
                # during development and teaching.
                logging.debug("Fetched weather payload: %s", payload)                               
                
                # Kafka messages are typically bytes or strings, not raw Python objects, 
                # so serialization is necessary.
                producer.produce(topic  = TOPIC_NAME,                                               # starts sending a Kafka message to the topic named in TOPIC_NAME
                                 key    = KEY_ID,                                                   # influence partitioning and helps identify the message stream
                                 value  = json.dumps(payload),)
                producer.flush()                                                                    # forces buffered messages to be sent to Kafka.

                # Logs successful delivery and states how long the script will sleep before the next iteration.
                logging.info("Message produced successfully. Sleeping for %d seconds ...", POLL_INTERVAL_SECONDS)
                
                # Pauses execution for 10 seconds. This creates the periodic polling behavior.
                time.sleep(POLL_INTERVAL_SECONDS)

            except requests.RequestException as exc:                                    # catches network-related and HTTP-related exceptions raised by requests
                logging.exception("Weather API request failed: %s", exc)                # logs the error message and stack trace
                
                # After an API failure, the script still waits 10 seconds before retrying.
                time.sleep(POLL_INTERVAL_SECONDS)                                       # prevents immediate tight-loop hammering of the API

            except KeyboardInterrupt:                                                   # catches manual interruption, such as pressing Ctrl + C
                logging.info("Interrupted by user. Stopping producer gracefully.")      # logs a clean shutdown message
                break                                                                   # exits the while True loop, which ends the producer run

            except Exception as exc:                                                    # catch-all for any other unexpected exception not handled earlier
                logging.exception("Unexpected error while producing to Kafka: %s", exc) # logs the unexpected failure and traceback for debugging
                time.sleep(POLL_INTERVAL_SECONDS)                                       # the script waits and then retries, rather than crashing immediately

# ================================================================================================= #
if __name__ == "__main__":

    logging.basicConfig(level       = getattr(logging, LOG_LEVEL.upper(), logging.INFO),    # configures the Python logging system
                        format="%(asctime)s | %(levelname)s | %(message)s",)                # sets the log message format so each log line includes
                                                                                            # time, severity level, and actual message text

    main()

# ================================================================================================= #