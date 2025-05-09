import json
import logging
import time
from datetime import datetime
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GBFS_URL = "https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json"
KAFKA_BOOTSTRAP_SERVERS = ['broker:9092']
KAFKA_TOPIC = 'lyft_station_status'
POLL_INTERVAL = 60

def fetch_station_status():
    """
    Fetch station status data from Lyft's GBFS API.
    
    Returns:
        dict: The JSON response from the API
    """
    try:
        response = requests.get(GBFS_URL, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None

def create_kafka_producer():
    """
    Create and return a Kafka producer instance.
    
    Returns:
        KafkaProducer: Configured Kafka producer
    """
    try:
        # Create producer that serializes data as JSON
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'  # Wait for all replicas to acknowledge
        )
    except KafkaError as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None

def on_send_success(record_metadata):
    """Callback for successful Kafka message delivery."""
    logger.info(f"Message delivered to {record_metadata.topic} "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]")

def on_send_error(exc):
    """Callback for failed Kafka message delivery."""
    logger.error(f"Message delivery failed: {exc}")

def main():
    """Main execution function."""
    producer = create_kafka_producer()
    if not producer:
        logger.error("Failed to create Kafka producer. Exiting.")
        return
    
    logger.info(f"Starting to poll {GBFS_URL} every {POLL_INTERVAL} seconds")
    
    try:
        while True:
            # Get current timestamp
            timestamp = datetime.now().isoformat()
            
            # Fetch data
            data = fetch_station_status()
            
            if data:
                # Add metadata
                enriched_data = {
                    "source": "lyft_gbfs",
                    "collected_at": timestamp,
                    "data": data
                }
                
                # Send to Kafka
                future = producer.send(
                    KAFKA_TOPIC,
                    value=enriched_data
                )
                future.add_callback(on_send_success).add_errback(on_send_error)
                
                # Make sure the message is sent before continuing
                producer.flush()
                
                logger.info(f"Data sent to Kafka topic {KAFKA_TOPIC}")
            else:
                logger.warning("No data fetched, skipping this iteration")
            
            # Wait for next polling interval
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted. Closing Kafka producer.")
    finally:
        # Clean up resources
        if producer:
            producer.close()
            logger.info("Kafka producer closed")

if __name__ == "__main__":
    main()