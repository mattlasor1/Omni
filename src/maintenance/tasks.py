import os
from celery import Celery
import numpy as np
import time

from src.memory.cache import LivestreamCache
from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor, RegressionEngine

# Initialize Celery app
# Point broker to Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://omnitwin-redis:6379/0")
celery_app = Celery("omnitwin_maintenance", broker=REDIS_URL)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Initialize interfaces
# In a real setup, models would be loaded from disk or artifact store.
# Using dummy dimensions for the prototype.
INPUT_DIM = 512  # E.g., embedding size of raw text/image
HIDDEN_DIM = 512
OUTPUT_DIM = 256 # E.g., parameter vector size

cache = LivestreamCache(host="omnitwin-redis")
wiki = SolidStateWiki(host="omnitwin-qdrant")
extractor = ParameterExtractor(input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, output_dim=OUTPUT_DIM)
regression_engine = RegressionEngine(learning_rate=0.05)


@celery_app.task(name="maintenance.process_cache_to_memory")
def process_cache_to_memory(batch_size: int = 100):
    """
    The core maintenance loop:
    1. Read raw signals from short-term cache.
    2. Pass through ParameterExtractor.
    3. Retrieve similar context from Vector DB.
    4. Regress new parameters against existing ones.
    5. Save updated state back to Vector DB.
    6. Acknowledge and clear cache.
    """
    print(f"Starting maintenance run. Fetching {batch_size} records...")
    messages = cache.read_stream(count=batch_size)
    
    if not messages:
        print("No new data in cache. Maintenance complete.")
        return "No data processed."

    processed_ids = []
    
    # messages format from redis-py xread:
    # [[b'stream_name', [(b'message_id', {b'field': b'value'})]]]
    for stream_name, stream_messages in messages:
        for msg_id, payload in stream_messages:
            msg_id_str = msg_id if isinstance(msg_id, str) else msg_id.decode('utf-8')
            
            try:
                # 1. Simulate parsing raw payload into a numerical representation
                # In production, this would involve LLM/Vision embedding APIs.
                print(f"Processing signal {msg_id_str}...")
                raw_vector = np.random.rand(INPUT_DIM).astype(np.float32) # Dummy vector for raw data
                
                # 2. Extract mathematical parameters
                new_parameters = extractor.extract(raw_vector)
                
                # 3. Retrieve similar contextual parameters from solid-state memory
                # We use the new parameters to find the 'neighborhood' of knowledge to update.
                similar_records = wiki.retrieve_similar(new_parameters, limit=1)
                
                if similar_records:
                    # 4. Regress against existing parameters
                    existing_parameters = np.array(similar_records[0].vector)
                    updated_parameters = regression_engine.regress(new_parameters, existing_parameters)
                    
                    # Store the updated parameters (in reality, might update existing point or create new trajectory)
                    wiki.store_parameters(updated_parameters, metadata={"source": "regression", "original_msg": payload.get('source_id', 'unknown')})
                    print(f"Regressed and updated parameters for {msg_id_str}")
                else:
                    # No similar context, store as completely new knowledge
                    wiki.store_parameters(new_parameters, metadata={"source": "novel_extraction", "original_msg": payload.get('source_id', 'unknown')})
                    print(f"Stored novel parameters for {msg_id_str}")
                    
                processed_ids.append(msg_id)
                
            except Exception as e:
                print(f"Error processing message {msg_id_str}: {e}")
                # Depending on error, might want to DLQ or retry. For now, continue.

    # 6. Clear processed data from cache
    if processed_ids:
        cache.acknowledge_and_delete(processed_ids)
        print(f"Maintenance complete. Integrated {len(processed_ids)} signals into Solid-State Wiki.")
        
    return f"Processed {len(processed_ids)} records."

# To simulate a periodic schedule, Celery beat can be configured to call this.
