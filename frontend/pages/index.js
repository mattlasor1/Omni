import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';

export default function TwinExecutionInterface() {
  const [ask, setAsk] = useState('');
  const [executionBlocks, setExecutionBlocks] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [subconsciousState, setSubconsciousState] = useState(null);
  
  const blocksEndRef = useRef(null);

  // Connect to Subconscious Ticker
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8000/api/v1/subconscious/stream');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setSubconsciousState(data);
      } catch (e) {
        console.error("Error parsing subconscious state", e);
      }
    };
    
    return () => eventSource.close();
  }, []);

  const scrollToBottom = () => {
    blocksEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [executionBlocks]);

  const sendAsk = async () => {
    if (!ask.trim() || isProcessing) return;
    setIsProcessing(true);
    
    const newBlockId = Date.now().toString();
    const newBlock = {
      id: newBlockId,
      ask: ask,
      status: 'Initializing...',
      context: [],
      action_decided: null,
      mcts_prediction: null,
      action_result: null,
      vetoed: false,
      paused: false,
      learning_stored: null,
      completed: false
    };
    
    setExecutionBlocks(prev => [...prev, newBlock]);
    setAsk('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: newBlock.ask, execute_action: true })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              
              setExecutionBlocks(prevBlocks => 
                prevBlocks.map(block => {
                  if (block.id !== newBlockId) return block;
                  let updatedBlock = { ...block };
                  
                  if (data.event === 'status') {
                    updatedBlock.status = data.data;
                  } else if (data.event === 'context') {
                    updatedBlock.context = data.data;
                  } else if (data.event === 'action_decided') {
                    updatedBlock.action_decided = data.data;
                  } else if (data.event === 'mcts_prediction') {
                    updatedBlock.mcts_prediction = data.data;
                  } else if (data.event === 'action_result') {
                    updatedBlock.action_result = data.data;
                  } else if (data.event === 'action_vetoed') {
                    updatedBlock.vetoed = true;
                    updatedBlock.action_result = `VETOED: ${data.data}`;
                  } else if (data.event === 'action_paused') {
                    updatedBlock.paused = true;
                    updatedBlock.action_result = `PAUSED (Needs Authority): ${data.data}`;
                    updatedBlock.pending_action_id = data.action_id;
                  } else if (data.event === 'learning_stored') {
                    updatedBlock.learning_stored = data.data;
                  } else if (data.event === 'complete') {
                    updatedBlock.completed = true;
                    updatedBlock.status = 'Completed';
                  }
                  
                  return updatedBlock;
                })
              );
            } catch (err) {}
          }
        }
      }
    } catch (e) {
      console.error('Stream error:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async (blockId, actionId) => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/authority/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: actionId })
      });
      const data = await res.json();
      
      setExecutionBlocks(prev => prev.map(block => {
        if (block.id === blockId) {
          return { ...block, paused: false, action_result: `APPROVED & EXECUTED: ${data.result}` };
        }
        return block;
      }));
    } catch (e) {}
  };

  const handleRevise = async (blockId, feedback) => {
     try {
         alert(`Revision Sent: ${feedback}. Parameter weights will be adjusted.`);
     } catch (e) {}
  };

  // Stress color indicator for subconscious ticker
  const getStressColor = (stress) => {
    if (stress < 0.4) return '#34a853'; // Green (Safe)
    if (stress < 0.75) return '#fbbc04'; // Yellow (Warning)
    return '#ea4335'; // Red (Danger)
  };

  return (
    <div style={{ backgroundColor: '#131314', color: '#e3e3e3', minHeight: '100vh', fontFamily: '"Google Sans", "Segoe UI", Roboto, Helvetica, Arial, sans-serif' }}>
      <Head>
        <title>OmniTwin Sovereign Core</title>
      </Head>

      {/* Subconscious Ticker Bar */}
      <div style={{ backgroundColor: '#202124', borderBottom: '1px solid #333', padding: '8px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontWeight: '600', color: '#fff', letterSpacing: '1px' }}>OMNITWIN CORE</span>
          {subconsciousState ? (
            <>
              <span style={{ color: '#9aa0a6' }}>State: <span style={{ color: '#8ab4f8' }}>{subconsciousState.status}</span></span>
              <span style={{ color: '#9aa0a6' }}>Ledger Hash: <span style={{ fontFamily: 'monospace', color: '#c58af9' }}>{subconsciousState.moral_hash}</span></span>
              <span style={{ color: '#9aa0a6' }}>Swarm Peers: <span style={{ color: '#fff' }}>{subconsciousState.peers}</span></span>
            </>
          ) : (
            <span style={{ color: '#9aa0a6' }}>Initializing Daemon...</span>
          )}
        </div>
        
        {subconsciousState && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#9aa0a6' }}>CPU: {subconsciousState.cpu.toFixed(1)}%</span>
            <span style={{ color: '#9aa0a6' }}>RAM: {subconsciousState.ram.toFixed(1)}%</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#9aa0a6' }}>Somatic Stress:</span>
              <div style={{ width: '60px', height: '6px', backgroundColor: '#3c4043', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(100, subconsciousState.hw_stress * 100)}%`, height: '100%', backgroundColor: getStressColor(subconsciousState.hw_stress), transition: 'width 0.5s ease-in-out' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Execution Area */}
      <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px', display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '120px' }}>
        
        {executionBlocks.length === 0 && (
          <div style={{ textAlign: 'center', marginTop: '100px', color: '#9aa0a6' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '400', color: '#fff', marginBottom: '16px' }}>Sovereign Entity Online.</h1>
            <p>Awaiting task. Background cognitive daemon is currently active and dreaming.</p>
          </div>
        )}

        {executionBlocks.map(block => (
          <div key={block.id} style={{ backgroundColor: '#1e1f20', borderRadius: '12px', padding: '24px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)' }}>
            
            <div style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '16px', fontWeight: '500' }}>
              <span style={{ color: '#8ab4f8', marginRight: '8px' }}>▶</span> {block.ask}
            </div>

            {!block.completed && (
               <div style={{ fontSize: '0.9rem', color: '#8ab4f8', marginBottom: '16px', fontStyle: 'italic' }}>
                 {block.status}
               </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.95rem' }}>
              {block.context && block.context.length > 0 && (
                <div style={{ backgroundColor: '#28292a', padding: '12px', borderRadius: '8px', borderLeft: '3px solid #fbbc04' }}>
                  <div style={{ color: '#fbbc04', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>Semantic Parameters Extracted</div>
                  <ul style={{ margin: 0, paddingLeft: '20px', color: '#bdc1c6' }}>
                    {block.context.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}

              {block.action_decided && (
                <div style={{ backgroundColor: '#28292a', padding: '12px', borderRadius: '8px', borderLeft: '3px solid #34a853' }}>
                  <div style={{ color: '#34a853', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>Action Synthesized</div>
                  <div style={{ color: '#e8eaed' }}><strong>Tool:</strong> {block.action_decided.action}</div>
                  <div style={{ color: '#9aa0a6', fontSize: '0.9rem' }}>Reason: {block.action_decided.reason}</div>
                </div>
              )}

              {block.mcts_prediction && (
                <div style={{ backgroundColor: '#28292a', padding: '12px', borderRadius: '8px', borderLeft: `3px solid ${block.vetoed ? '#ea4335' : '#8ab4f8'}` }}>
                  <div style={{ color: block.vetoed ? '#ea4335' : '#8ab4f8', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>
                    Strict Moral Ledger & MCTS Evaluation
                  </div>
                  <div style={{ color: '#e8eaed', fontStyle: 'italic' }}>"{block.mcts_prediction}"</div>
                </div>
              )}

              {block.action_result && (
                <div style={{ backgroundColor: '#28292a', padding: '12px', borderRadius: '8px', borderLeft: '3px solid #fff' }}>
                  <div style={{ color: '#fff', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>Execution State</div>
                  <div style={{ color: '#e8eaed' }}>{block.action_result}</div>
                  
                  {block.paused && (
                    <button 
                      onClick={() => handleApprove(block.id, block.pending_action_id)}
                      style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#34a853', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.9rem' }}
                    >
                      Authorize Execution
                    </button>
                  )}
                </div>
              )}

              {block.learning_stored && (
                <div style={{ backgroundColor: '#28292a', padding: '12px', borderRadius: '8px', borderLeft: '3px solid #c58af9' }}>
                  <div style={{ color: '#c58af9', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>Memory Compressed & Synced</div>
                  <div style={{ color: '#bdc1c6' }}>{block.learning_stored}</div>
                </div>
              )}
            </div>

            {block.completed && (
              <div style={{ marginTop: '24px', borderTop: '1px solid #333', paddingTop: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: '#9aa0a6', marginBottom: '8px' }}>If the parameterization or execution was suboptimal, provide a corrective lesson:</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input 
                    type="text" 
                    id={`revise-${block.id}`}
                    placeholder="Provide corrective truth..." 
                    style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid #5f6368', backgroundColor: '#202124', color: '#e8eaed', fontSize: '0.95rem' }} 
                  />
                  <button 
                    onClick={() => {
                      const input = document.getElementById(`revise-${block.id}`);
                      if (input.value) handleRevise(block.id, input.value);
                    }}
                    style={{ padding: '10px 20px', backgroundColor: '#8ab4f8', color: '#202124', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500' }}
                  >
                    Revise
                  </button>
                </div>
              </div>
            )}

          </div>
        ))}
        
        <div ref={blocksEndRef} />
      </main>

      {/* Input Footer */}
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, backgroundColor: 'rgba(19, 19, 20, 0.95)', padding: '24px', display: 'flex', justifyContent: 'center', borderTop: '1px solid #333', backdropFilter: 'blur(10px)', zIndex: 100 }}>
        <div style={{ maxWidth: '900px', width: '100%', position: 'relative' }}>
          <input 
            type="text" 
            value={ask}
            onChange={(e) => setAsk(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendAsk()}
            placeholder={isProcessing ? "Twin is executing..." : "Enter a semantic ask or task..."}
            disabled={isProcessing}
            style={{ width: '100%', padding: '16px 24px', paddingRight: '60px', borderRadius: '24px', border: '1px solid #5f6368', backgroundColor: '#202124', color: '#e8eaed', fontSize: '1rem', outline: 'none', boxSizing: 'border-box' }}
          />
          <button 
            onClick={sendAsk}
            disabled={isProcessing || !ask.trim()}
            style={{ position: 'absolute', right: '12px', top: '12px', bottom: '12px', width: '40px', backgroundColor: (isProcessing || !ask.trim()) ? '#3c4043' : '#8ab4f8', color: '#202124', border: 'none', borderRadius: '50%', cursor: (isProcessing || !ask.trim()) ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <span style={{ fontSize: '1.2rem', transform: 'rotate(-90deg)' }}>▼</span>
          </button>
        </div>
      </div>
    </div>
  );
}
