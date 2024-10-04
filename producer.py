from kafka import KafkaProducer
from kafka_config import KAFKA_PRODUCER_CONFIG

producer = KafkaProducer(**KAFKA_PRODUCER_CONFIG)

def send_user_activity(user_id: int, activity: str):
    producer.send('user-activity', key=str(user_id).encode(), value=activity.encode())
