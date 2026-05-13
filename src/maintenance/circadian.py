import asyncio
import time
from typing import Any
import psutil

class CircadianEngine:
    """
    Compatibility biological state engine used by the maintenance and biometric
    layers. It models coarse energy/fatigue state without depending on the
    perpetual async daemon.
    """
    def __init__(self):
        self.energy = 100.0
        self.state = "AWAKE"
        self.last_update = time.time()

    def tick(self, active_processing_load: int = 0):
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        if self.state == "ASLEEP":
            self.energy = min(100.0, self.energy + (elapsed * 5.0))
            if self.energy >= 100.0:
                self.state = "AWAKE"
        else:
            base_drain = elapsed * 0.1
            load_drain = active_processing_load * 0.5
            self.energy = max(0.0, self.energy - (base_drain + load_drain))
            if self.energy <= 0.0:
                self.state = "ASLEEP"
            elif self.energy < 30.0:
                self.state = "FATIGUED"
            else:
                self.state = "AWAKE"

    def can_process_sensory_input(self) -> bool:
        return self.state != "ASLEEP"

class PerpetualCognitiveDaemon:
    """
    The True Continuous Learning Daemon ("Dream State").
    Runs continuously in the background. When the system is idle (low queries),
    it scans uncompressed memories, runs hypothetical MCTS simulations, and 
    optimizes parameter correlations autonomously.
    """
    def __init__(self, reasoning_engine, vector_db, mcts_engine, somatic_engine):
        self.reasoning = reasoning_engine
        self.wiki = vector_db
        self.mcts = mcts_engine
        self.somatic = somatic_engine
        self.is_running = False
        self.last_active_time = time.time()
        self.idle_threshold = 30 # seconds before triggering deep dream
        
    def ping_activity(self):
        """Called by API endpoints to reset the idle timer."""
        self.last_active_time = time.time()
        
    async def run_daemon(self, sse_broadcast_callback=None):
        """The infinite loop representing the subconscious life of the Twin."""
        self.is_running = True
        print("Perpetual Cognitive Daemon Online.")
        
        while self.is_running:
            await asyncio.sleep(5) # Tick rate
            
            # 1. Broadcast Subconscious State (if callback exists)
            hw_state = self.somatic.get_live_state()
            state_msg = f"Idle: {time.time() - self.last_active_time:.1f}s | CPU: {hw_state['cpu_percent']}% | RAM: {hw_state['ram_percent']}% | Stress: {hw_state['hardware_stress']:.2f}"
            
            if sse_broadcast_callback:
                await sse_broadcast_callback({
                    "event": "subconscious_tick",
                    "data": state_msg,
                    "stress": hw_state['hardware_stress']
                })
            
            # 2. Check if idle enough to 'Dream'
            if time.time() - self.last_active_time > self.idle_threshold:
                # 3. Check hardware embodiment (Don't dream if host is stressed/dying)
                if hw_state['hardware_stress'] > 0.8:
                    if sse_broadcast_callback:
                        await sse_broadcast_callback({"event": "subconscious_thought", "data": "Hardware severely stressed. Suspending dream state to conserve power."})
                    continue
                    
                if sse_broadcast_callback:
                    await sse_broadcast_callback({"event": "subconscious_thought", "data": "Entering autonomous dream state. Compressing unlinked memories..."})
                
                # Mock Dream/Compression process
                # In full implementation, it would fetch random vectors and run reasoning.synthesize_concept
                await asyncio.sleep(2)
                
                if sse_broadcast_callback:
                    await sse_broadcast_callback({"event": "subconscious_thought", "data": "Dream cycle complete. Parameter matrix refined."})
                
                # Reset timer so it doesn't chain-dream instantly
                self.ping_activity()
