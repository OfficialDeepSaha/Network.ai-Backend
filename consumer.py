from kafka import KafkaConsumer
from kafka_config import KAFKA_CONSUMER_CONFIG
import json

consumer = KafkaConsumer('user-activity', **KAFKA_CONSUMER_CONFIG, value_deserializer=lambda v: json.loads(v.decode('utf-8')))

def process_activity(user_id, activity):
    """Process user activity for real-time actions"""
    print(f"Processing activity for user {user_id}: {activity}")
    # Implement logic based on activity type, e.g., notify user, update dashboard, etc.

# Continuously consume Kafka messages
for message in consumer:
    process_activity(message.key.decode(), message.value['activity'])

