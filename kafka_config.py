from settings import KAFKA_SERVERS

KAFKA_PRODUCER_CONFIG = {
    'bootstrap_servers': ['localhost:9092']  # Ensure this is the correct address
}

KAFKA_CONSUMER_CONFIG = {
    'bootstrap_servers': KAFKA_SERVERS,
    'group_id': 'my-group',
    'auto_offset_reset': 'earliest'
}
