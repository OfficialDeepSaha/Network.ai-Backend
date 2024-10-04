from kafka import KafkaProducer
from kafka.errors import KafkaError
from kafka_config import KAFKA_PRODUCER_CONFIG
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_PRODUCER_CONFIG['bootstrap_servers'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),  # Serialize data to JSON
        key_serializer=lambda k: str(k).encode('utf-8')
    )
    logger.info("Kafka producer initialized successfully")
except KafkaError as e:
    logger.error(f"Failed to initialize Kafka producer: {e}")
    producer = None  # Optionally, handle what should happen if Kafka isn't available

def send_user_activity(user_id: int, activity: str):
    """Send real-time user activity to Kafka."""
    if producer is None:
        return {"error": "Kafka producer not initialized"}

    message = {
        "user_id": user_id,
        "activity": activity
    }

    try:
        # Send the message to the Kafka topic
        future = producer.send('user-activity', key=str(user_id), value=message)
        producer.flush()  # Ensure the message is sent
        future.get(timeout=10)  # Optional: Wait for the message to be sent and handle any errors
        logger.info(f"Sent user activity to Kafka: {message}")
        return {"message": "User activity sent to Kafka"}
    except KafkaError as e:
        logger.error(f"Failed to send message to Kafka: {e}")
        return {"error": "Failed to send message to Kafka"}

