import os
from celery import Celery
import numpy as np
from sklearn.cluster import DBSCAN
import time

from src.memory.cache import LivestreamCache
from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor, ContinualRegressionEngine
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.curiosity import CuriosityEngine
from src.memory.graph_db import CausalGraphMemory
from src.learning.state import InternalStateEngine
from src.maintenance.circadian import CircadianEngine
from src.learning.epistemology import BayesianEngine
from src.maintenance.nemesis import AdversarialNemesisEngine
from src.learning.self_play import SyntheticRehearsalEngine
from src.learning.cross_pollination import TensorCrossPollinator
from src.execution.seeker import SeekerSwarm

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("omnitwin_maintenance", broker=REDIS_URL)
celery_app.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json', timezone='UTC', enable_utc=True)

from src.swarm.sync import SwarmProtocol

# Lazily initialized to prevent issues in worker startup
cache = None
wiki = None
graph = None
extractor = None
regression_engine = None
reasoning_engine = None
curiosity_engine = None
swarm = None
state_engine = None
circadian_engine = None
bayesian_engine = None
nemesis = None
self_play = None
pollinator = None
seeker = None

def init_interfaces():
    global cache, wiki, graph, extractor, regression_engine, reasoning_engine, curiosity_engine, swarm, state_engine, circadian_engine, bayesian_engine, nemesis, self_play, pollinator, seeker
    if cache is None:
        cache = LivestreamCache(host=os.getenv("REDIS_HOST", "localhost"))
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
        graph = CausalGraphMemory()
        extractor = ParameterExtractor(output_dim=256)
        regression_engine = ContinualRegressionEngine(learning_rate=0.05, memory_preservation=0.8)
        reasoning_engine = CognitiveReasoningEngine()
        curiosity_engine = CuriosityEngine(reasoning_engine)
        swarm = SwarmProtocol(wiki)
        state_engine = InternalStateEngine()
        circadian_engine = CircadianEngine()
        bayesian_engine = BayesianEngine()
        nemesis = AdversarialNemesisEngine(wiki, reasoning_engine, cache)
        self_play = SyntheticRehearsalEngine(wiki, reasoning_engine, cache)
        pollinator = TensorCrossPollinator(wiki, graph)
        seeker = SeekerSwarm(cache, reasoning_engine)

@celery_app.task(name="maintenance.nemesis_strike")
def trigger_nemesis():
    init_interfaces()
    nemesis.strike()
    return "Nemesis task completed."

@celery_app.task(name="maintenance.process_cache_to_memory")
def process_cache_to_memory(batch_size: int = 100):
    """
    Ingests cache -> Extracts Math -> Regresses against Episodic Memory.
    """
    init_interfaces()
    
    # Check Biological State
    circadian_engine.tick(active_processing_load=0)
    if not circadian_engine.can_process_sensory_input():
        print("Circadian Sleep Phase: Ignoring sensory ingestion to focus on consolidation.")
        return "Asleep. Ingestion paused."
        
    print(f"Starting ingestion maintenance. Fetching {batch_size} records...")
    messages = cache.read_stream(count=batch_size)
    
    if not messages:
        return "No data processed."

    processed_ids = []
    
    for stream_name, stream_messages in messages:
        for msg_id, payload in stream_messages:
            try:
                data_type = payload.get("type", "text")
                raw_content = payload.get("content", "")
                
                # Extract mathematical parameters using multi-modal model
                new_parameters = extractor.extract(data_type, raw_content)
                
                # Store directly to episodic memory to represent raw experience
                wiki.store_episodic(new_parameters, metadata={"source_id": payload.get('source_id', 'unknown'), "content": raw_content[:200], "type": data_type})
                processed_ids.append(msg_id)
                
            except Exception as e:
                print(f"Error processing message {msg_id}: {e}")

    if processed_ids:
        cache.acknowledge_and_delete(processed_ids)
        print(f"Maintenance complete. Integrated {len(processed_ids)} signals into Episodic Memory.")
        
        # Update emotional stress based on remaining queue
        try:
            stream_info = cache.client.xinfo_stream(cache.stream_key)
            state_engine.update_stress(stream_info.get('length', 0))
            circadian_engine.tick(active_processing_load=len(processed_ids))
        except:
            pass
            
    # Check for Merovingian shift during normal ingestion mapping
    if state_engine.check_merovingian_shift():
        # Inject an arbitrary learning task to break fixation
        autonomous_reflection.delay(sample_size=50, force_merovingian=True)
        
    return f"Processed {len(processed_ids)} records."

@celery_app.task(name="maintenance.autonomous_reflection")
def autonomous_reflection(sample_size: int = 500, force_merovingian: bool = False):
    """
    The 'Dream' State.
    Scans episodic memory, clusters related thoughts, uses LLM to synthesize abstract concepts,
    and stores them in Semantic Memory.
    """
    init_interfaces()
    print("Initiating Autonomous Reflection Loop...")
    
    # 1. Fetch recent episodic memories
    try:
        vectors, payloads = wiki.fetch_all_episodic(limit=sample_size)
        if len(vectors) < 5:
            return "Not enough episodic memory to reflect upon."
    except Exception as e:
        print(f"Reflection failed to fetch memory: {e}")
        return "Fetch failed."

    # Merovingian Injection: If forced, pick a random historical semantic concept 
    # and pull its causal chain to force a tangential abstraction instead of normal clustering.
    if force_merovingian:
        print("Executing Merovingian Tangent Reflection...")
        # Get random semantic nodes to force a shift
        import random
        try:
            random_points = wiki.client.scroll(collection_name=wiki.semantic_collection, limit=10, with_vectors=True)[0]
            if random_points:
                target = random.choice(random_points)
                # Walk the graph slightly to find a tangent
                chain = graph.get_causal_chain(target.id)
                tangent_payloads = [{"content": c["attributes"].get("concept", "Chaos signal")} for c in chain]
                if tangent_payloads:
                    vectors = [np.array(target.vector)] # Dummy to pass loop
                    payloads = tangent_payloads * len(vectors) # Force context
        except Exception as e:
            print(f"Merovingian extraction failed: {e}")

    # 2. Cluster memories mathematically using DBSCAN to find related concepts
    # (If merovingian triggered, vectors might just be the hijacked tangent)
    clustering = DBSCAN(eps=0.3, min_samples=3 if not force_merovingian else 1, metric='cosine').fit(vectors)
    labels = clustering.labels_
    
    unique_clusters = set(labels)
    synthesized_count = 0
    
    for cluster_id in unique_clusters:
        if cluster_id == -1: continue # Noise
        
        # 3. Gather the cluster
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_payloads = [payloads[i] for i in cluster_indices]
        
        # 4. Cognitive Synthesis via LLM
        # If Merovingian, append instructions to find a tangential connection
        if force_merovingian:
            cluster_payloads.append({"content": "MEROVINGIAN DIRECTIVE: Find a completely novel, tangential perspective based on this data to break current cognitive fixation."})
            
        synthesis = reasoning_engine.synthesize_concept(cluster_payloads)
        concept_text = synthesis.get("concept", "")
        
        if concept_text and concept_text != "Synthesis error":
            # 5. Extract math parameters for the newly formed abstract concept
            semantic_parameters = extractor.extract("text", concept_text)
            
            # 6. Regress against existing semantic memory
            similar_semantic = wiki.retrieve_similar(semantic_parameters, collection=wiki.semantic_collection, limit=1)
            
            if similar_semantic:
                existing_point = similar_semantic[0]
                existing_params = np.array(existing_point.vector)
                
                # Bayesian Update
                alpha = existing_point.payload.get("bayes_alpha", 1.0)
                beta = existing_point.payload.get("bayes_beta", 1.0)
                depth = existing_point.payload.get("fractal_depth", 0)
                
                # Check if this was a nemesis injection (negative evidence)
                is_nemesis = any(c.get("context", {}).get("nemesis_injection") for c in cluster_payloads if "context" in c)
                
                if is_nemesis:
                    new_alpha, new_beta = bayesian_engine.bayesian_update(alpha, beta, positive_evidence=0.0, negative_evidence=1.0)
                else:
                    new_alpha, new_beta = bayesian_engine.bayesian_update(alpha, beta, positive_evidence=1.0, negative_evidence=0.0)
                    
                # Calculate surprise based on new Bayesian epistemology
                surprise = bayesian_engine.compute_surprise(alpha, beta, 0.0 if is_nemesis else 1.0)
                
                # Apply emotional state modifiers to learning rate
                state_mod = state_engine.get_learning_rate_modifier()
                updated_params, _ = regression_engine.regress(semantic_parameters, existing_params, state_modifier=state_mod)
                
                # Overwrite existing point with updated bayes params
                metadata = {"concept": concept_text, "surprise_score": surprise, "bayes_alpha": new_alpha, "bayes_beta": new_beta, "fractal_depth": depth + 1}
                sem_id = wiki.store_semantic(updated_params, metadata=metadata, point_id=existing_point.id)
                final_vector = updated_params
                print(f"Updated semantic concept (Fractal Depth {depth+1}). Bayesian Surprise: {surprise:.2f}")
            else:
                surprise = 1.0
                sem_id = wiki.store_semantic(semantic_parameters, metadata={"concept": concept_text, "surprise_score": 1.0})
                final_vector = semantic_parameters
                print("Formed novel semantic concept.")
                
            # Add to Causal Graph
            graph.add_event(sem_id, {"type": "semantic", "concept": concept_text})
            
            # Swarm Sync (Broadcast to Peers)
            swarm.broadcast_new_semantic_concept(sem_id, final_vector.tolist(), {"concept": concept_text})
            
            # If surprise is unusually high (anomalous data/confusion), trigger Curiosity
            if surprise > 0.8:
                question = curiosity_engine.evaluate_cluster_for_curiosity(cluster_payloads)
                if question:
                    print(f"Curiosity Triggered! Twin asks: {question}")
                    # Push to UI Stream
                    if cache:
                        cache.client.xadd("omnitwin:curiosity:stream", {"question": question, "related_concept_id": sem_id})
                    
                    # Exponential Growth: Immediately dispatch seekers to resolve the gap
                    seeker.dispatch_seekers(question)
                        
            synthesized_count += 1
            
    return f"Reflection complete. Synthesized {synthesized_count} abstract concepts from episodic clusters."

@celery_app.task(name="maintenance.exponential_growth_cycle")
def exponential_growth_cycle():
    """
    Runs background intelligence acceleration processes.
    - Synthetic Self-Play (Internal data generation)
    - Cross-Domain Pollination (Hidden correlation mapping)
    """
    init_interfaces()
    print("Initiating Exponential Growth Cycle...")
    
    # Run Self-Play
    self_play.execute_self_play()
    
    # Run Epiphany Pollinator
    epiphanies = pollinator.run_pollination_cycle()
    if epiphanies > 0 and cache:
        cache.client.incrby("omnitwin:metrics:epiphanies", epiphanies)
        
    return f"Growth cycle complete. {epiphanies} epiphanies mapped."
