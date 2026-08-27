# ================================================================================================= #
# Filename  : Tutorial_02_Quixstreams.py
#
# Purpose   : Demonstrate how to consume messages from an Apache Kafka topic using Python and
#             Quix Streams, then decode and inspect each incoming JSON event step-by-step.
#
# Commands  : Make sure Kafka is running locally (default broker: localhost:9092).
#             In CMD >> kafka-server-start.bat C:\kafka\config\kraft\server.properties
#
#             First run the producer from Tutorial_01_Quixstreams.py so that messages are available
#             in the topic 'weather_data_demo'.
#
#             To run this tutorial, >> python Tutorial_02_Quixstreams.py
#
# Remarks   : 1. This tutorial acts as a Kafka consumer.
#             2. It subscribes to the topic produced in Tutorial 01 and continuously polls Kafka
#                for new records.
#             3. Each consumed message is decoded from JSON and displayed in a human-readable form.
#             4. Offsets are stored only after successful processing, which is a good habit for
#                reliable stream processing.
#             5. The script is intentionally simple so that it can serve as an introductory Kafka
#                consumer example in a Quix Streams-based Data Engineering tutorial series.
#
# Reference : https://www.youtube.com/@QuixStreams
#
# Composer  : Dr. Hassan Mohy-ud-Din
# Email     : hassan.mohyuddin@lums.edu.pk
# Date      : March 28, 2026
# ================================================================================================= #

import os, json, logging

from quixstreams                        import Application

# ================================================================================================= #
# Global constants used by the tutorial.
DEFAULT_BROKER_ADDRESS              = os.getenv("KAFKA_BROKER", "localhost:9092")                   # if environment variable KAFKA_BROKER exists, otherwise default to "localhost:9092"
DEFAULT_CONSUMER_GROUP              = os.getenv("KAFKA_CONSUMER_GROUP", "weather-consumer-demo")    # consumer group from the environment variable or the default value
LOG_LEVEL                           = "DEBUG"                                                       # desired logging verbosity; DEBUG means the script will print detailed diagnostic information
TOPIC_NAME                          = "weather_data_demo"                                           # kafka topic to which weather messages will be published
POLL_TIMEOUT_SECONDS                = 1.0                                                           # consumer asks Kafka for a message, it will wait up to 1 second before returning
AUTO_OFFSET_RESET                   = "earliest"                                                    # start reading from the beginning of the topic, not just from newly arriving messages

# ================================================================================================= #
def decode_bytes(value):
    """
    Convert Kafka bytes to a UTF-8 string when needed.
    UTF-8 is a variable-length character encoding for Unicode that uses 1-4 bytes per character, 
    compatible with ASCII.
    
    Remark: Invalid bytes are sequences in a bytes object that cannot be interpreted according 
            to a text encoding like UTF-8, often caused by corruption, wrong encoding assumptions 
            (ISO 8859-1 or Windows-1252), partial/missing data (multi-byte character might be split 
            across chunks; decoding an incomplete byte sequence), or binary data (images, audio files;
            that do not represent text). 
            Using errors = "replace" safely decodes such bytes by substituting them with a 
            placeholder instead of raising an error.
    """
    if value is None            : return None
    if isinstance(value, bytes) : return value.decode("utf-8", errors = "replace")                  # input is a bytes object, decode it using UTF-8
                                                                                                    # if there are invalid byte sequences, replace them instead of crashing
    return str(value)

# ================================================================================================= #
def parse_json_message(raw_value):
    """
    Parse the Kafka message value from bytes/string into a Python dictionary.
    """
    decoded_value                   = decode_bytes(raw_value)                                       # first converts the raw Kafka value into a text string
    return json.loads(decoded_value)                                                                # parses the decoded JSON string into a Python dictionary
                                                                                                    # if the string is not valid JSON, this line raises json.JSONDecodeError, which is handled later in main()

# ================================================================================================= #
def display_weather_message(message_key, payload, kafka_metadata):
    """
    Print the most useful pieces of the weather event in a readable form.
    """
    # From the outer payload dictionary, this extracts the nested "weather_response" field.
    weather                         = payload.get("weather_response", {})                           # payload is a collection of key-value pairs
    
    # From inside the weather response, this extracts the "current_weather" dictionary.
    current_weather                 = weather.get("current_weather", {})

    # Starts an info log line that reports where in Kafka this message came from.
    logging.info("Consumed message from topic='%s', partition=%s, offset=%s",
                 kafka_metadata["topic"], kafka_metadata["partition"], kafka_metadata["offset"])
    
    logging.info("Message key               : %s", message_key)                                     # Kafka key
    logging.info("City                      : %s", payload.get("city"))
    logging.info("Source                    : %s", payload.get("source"))
    logging.info("Collected at (unix)       : %s", payload.get("collected_at_unix"))                # Unix timestamp showing when the producer created the event
    logging.info("Temperature               : %s", current_weather.get("temperature"))
    logging.info("Wind speed                : %s", current_weather.get("windspeed"))
    logging.info("Wind direction            : %s", current_weather.get("winddirection"))
    logging.info("Weather code              : %s", current_weather.get("weathercode"))
    logging.info("Observed time             : %s", current_weather.get("time"))
    logging.info("-" * 100)

# ================================================================================================= #
def main():
    """Build a Quix Streams application object. Here, we use it only for consumer-side interaction."""

    # Creates a Quix Streams Application object and gives it the Kafka broker address.
    app                             = Application(broker_address    = DEFAULT_BROKER_ADDRESS,
                                                  consumer_group    = DEFAULT_CONSUMER_GROUP,       # Important! Kafka tracks offsets per consumer group
                                                  auto_offset_reset = AUTO_OFFSET_RESET,            # tells consumer how to start if no offset is already committed
                                                  loglevel          = LOG_LEVEL,)                   # set the internal log level

    logging.info("Connecting to Kafka broker at %s" , DEFAULT_BROKER_ADDRESS)                       # which Kafka broker the script is trying to connect to
    logging.info("Using consumer group '%s'"        , DEFAULT_CONSUMER_GROUP)                       # logs the consumer group name
    logging.info("Subscribing to topic '%s'"        , TOPIC_NAME)                                   # logs the topic that the consumer will subscribe to

    # The consumer is a read-only Kafka connection used to receive records from a topic.
    # auto_commit_enable = True means offset commits are enabled automatically, but the 
    # code still uses store_offsets(...) so offsets are marked only after processing.
    with app.get_consumer(auto_commit_enable = True) as consumer:

        # Subscribes the consumer to the topic list containing only weather_data_demo.
        consumer.subscribe(topics = [TOPIC_NAME])

        while True:
            try:
                msg                 = consumer.poll(timeout = POLL_TIMEOUT_SECONDS)                 # asks Kafka for one message, waiting up to 1 second

                if msg is None: continue                                                            # no message arrived during the timeout, skip the rest of this loop iteration and poll again
                
                # Kafka returned a message-like object that represents an error.
                # End of partition  : KafkaError{code=_PARTITION_EOF    , val=-191, str="Broker : No more messages"}
                # Timeout           : KafkaError{code=_TIMED_OUT        , val=-185, str="Local  : Timed out"}
                # Broker issue      : KafkaError{code=_ALL_BROKERS_DOWN , val=-187, str="Local  : All broker connections are down"}
                if msg.error():
                    logging.error("Kafka consumer error: %s", msg.error())
                    continue
                
                # Reads the Kafka message key and converts it into a string if needed.
                message_key         = decode_bytes(msg.key())

                # Reads the Kafka message value, decodes it from bytes, and parses it from JSON into a Python dictionary.
                payload             = parse_json_message(msg.value())

                # Build a small metadata dictionary containing Kafka-specific information.
                kafka_metadata      = {"topic"     : msg.topic(),                                   # stores the topic name
                                       "partition" : msg.partition(),                               # partition number from which the message was read
                                       "offset"    : msg.offset(),}                                 # message offset

                # Print the parsed weather information and metadata in a readable format.
                display_weather_message(message_key, payload, kafka_metadata)

                # Mark this message as processed so the consumer can commit its offset later.
                consumer.store_offsets(message = msg)                                               # we successfully handled this message, so its offset may now be committed

            except json.JSONDecodeError as exc:
                logging.exception("Failed to decode JSON payload: %s", exc)

            except KeyboardInterrupt:
                logging.info("Interrupted by user. Stopping consumer gracefully.")
                break                                                                               # with block closes the consumer cleanly

            except Exception as exc:
                logging.exception("Unexpected error while consuming from Kafka: %s", exc)

# ================================================================================================= #
if __name__ == "__main__":

    logging.basicConfig(level       = getattr(logging, LOG_LEVEL.upper(), logging.INFO),            # configures the Python logging system
                        format      = "%(asctime)s | %(levelname)s | %(message)s",)                 # sets the log message format so each log line includes
                                                                                                    # time, severity level, and actual message text

    main()

# ================================================================================================= #