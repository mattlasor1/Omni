import { useState, useEffect } from 'react';

export default function TrainingArena() {
  const [query, setQuery] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [stats, setStats] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [graftSource, setGraftSource] = useState('');
  const [graftTarget, setGraftTarget] = useState('');
  const [authQueue, setAuthQueue] = useState([]);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/state');
      const data = await res.json();
      setStats(data);
      
      const graphRes = await fetch('http://localhost:8000/api/v1/coprocessing/graph');
      const gData = await graphRes.json();
      setGraphData(gData);
      
      const authRes = await fetch('http://localhost:8000/api/v1/authority/queue');
      const authData = await authRes.json();
      setAuthQueue(authData.queue || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleGraft = async () => {
    if (!graftSource || !graftTarget) return;
    try {
      await fetch('http://localhost:8000/api/v1/coprocessing/graft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_id: graftSource, target_id: graftTarget })
      });
      alert('Neural Link Graft Successful!');
      setGraftSource('');
      setGraftTarget('');
    } catch (e) {
      console.error(e);
    }
  };

  const handleApproveAction = async (actionId) => {
    try {
      await fetch('http://localhost:8000/api/v1/authority/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: actionId })
      });
      alert('Action Approved and Executed!');
      fetchStats();
    } catch (e) {
      console.error(e);
    }
  };

  const sendQuery = async () => {
    if (!query) return;
    setChatLog((prev) => [...prev, { role: 'user', content: query }]);
    const currentQuery = query;
    setQuery('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery, execute_action: true })
      });
      const data = await res.json();
      setChatLog((prev) => [
        ...prev,
        { role: 'twin', content: data.response, process: data.process_used, contextIds: data.context_ids, mcts: data.mcts_simulation }
      ]);
    } catch (e) {
      console.error(e);
    }
  };

  const sendFeedback = async (memoryIds, score) => {
    try {
      await fetch('http://localhost:8000/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_ids: memoryIds, reward_score: score })
      });
      alert('Moral Alignment Feedback registered!');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50' }}>OmniTwin RLHF Training Arena</h1>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        {/* Chat / Interaction Pane */}
        <div style={{ flex: 2, border: '1px solid #ccc', borderRadius: '8px', padding: '20px', background: '#f9f9f9' }}>
          <h2>Generative Alignment</h2>
          <div style={{ height: '400px', overflowY: 'auto', marginBottom: '20px', background: '#fff', padding: '10px', border: '1px solid #eee' }}>
            {chatLog.map((msg, idx) => (
              <div key={idx} style={{ marginBottom: '15px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                <span style={{
                  background: msg.role === 'user' ? '#3498db' : '#ecf0f1',
                  color: msg.role === 'user' ? '#fff' : '#333',
                  padding: '10px 15px',
                  borderRadius: '20px',
                  display: 'inline-block',
                  maxWidth: '80%'
                }}>
                  {msg.process && <span style={{ fontSize: '0.7em', background: '#e74c3c', color: 'white', padding: '2px 5px', borderRadius: '4px', marginRight: '5px' }}>{msg.process}</span>}
                  {msg.content}
                </span>
                
                {msg.mcts && (
                    <div style={{ marginTop: '5px', fontSize: '0.75em', background: '#2c3e50', color: '#ecf0f1', padding: '8px', borderRadius: '4px', textAlign: 'left' }}>
                      <strong>MCTS World Model Simulation:</strong><br/>
                      <i>{msg.mcts}</i>
                    </div>
                )}
                
                {msg.role === 'twin' && msg.contextIds && msg.contextIds.length > 0 && (
                  <div style={{ marginTop: '5px' }}>
                    <button onClick={() => sendFeedback(msg.contextIds, 1.0)} style={{ background: '#2ecc71', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', marginRight: '5px' }}>Approve (+1)</button>
                    <button onClick={() => sendFeedback(msg.contextIds, -1.0)} style={{ background: '#e74c3c', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Reject Moral (-1)</button>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="text" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && sendQuery()}
              style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }} 
              placeholder="Test the Twin's alignment..." 
            />
            <button onClick={sendQuery} style={{ padding: '10px 20px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Send</button>
          </div>
        </div>

        {/* Live Metrics Pane */}
        <div style={{ flex: 1, background: '#2c3e50', color: 'white', padding: '20px', borderRadius: '8px' }}>
          <h2>Live Telemetry</h2>
          {stats ? (
            <div>
              <p><strong>Semantic Abstractions:</strong> {stats.semantic_points}</p>
              <p><strong>Epistemic Uncertainty:</strong> {stats.avg_uncertainty}</p>
              <p><strong>Fractal Depth:</strong> {stats.avg_fractal_depth}</p>
              <hr style={{ borderColor: '#34495e' }}/>
              <p><strong>Biological State:</strong> {stats.biological_state}</p>
              <p><strong>Stress:</strong> {stats.emotional_state.stress}</p>
              <p><strong>Arousal:</strong> {stats.emotional_state.arousal}</p>
              <p><strong>Fixation:</strong> {stats.emotional_state.fixation}</p>
            </div>
          ) : (
            <p>Connecting to OmniCore...</p>
          )}
          
          <hr style={{ borderColor: '#34495e', marginTop: '20px' }}/>
          <h2>Symbiotic Co-Processing (Neural Link)</h2>
          <p style={{ fontSize: '0.8em', color: '#bdc3c7' }}>Manually graft causal links into the Twin's graph memory.</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input type="text" placeholder="Source Node ID" value={graftSource} onChange={e => setGraftSource(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: 'none' }} />
            <input type="text" placeholder="Target Node ID" value={graftTarget} onChange={e => setGraftTarget(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: 'none' }} />
            <button onClick={handleGraft} style={{ background: '#9b59b6', color: 'white', border: 'none', padding: '10px', borderRadius: '4px', cursor: 'pointer' }}>Graft Logic</button>
          </div>
          
          {graphData && (
             <div style={{ marginTop: '20px', fontSize: '0.75em', background: '#1a252f', padding: '10px', borderRadius: '4px', maxHeight: '200px', overflowY: 'auto' }}>
               <strong>Live Causal Nodes:</strong>
               {graphData.nodes.map(n => <div key={n.id} style={{ color: '#2ecc71' }}>ID: {n.id.substring(0,6)}... - {n.label}</div>)}
             </div>
          )}
          
          {authQueue.length > 0 && (
            <div style={{ marginTop: '20px', background: '#e74c3c', color: 'white', padding: '15px', borderRadius: '4px' }}>
              <h3>⚠️ Actions Awaiting Authority</h3>
              <p style={{ fontSize: '0.8em' }}>High-risk / Low-confidence actions require your explicit cryptographic approval.</p>
              {authQueue.map(item => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>
                  <span>{item.action}</span>
                  <button onClick={() => handleApproveAction(item.id)} style={{ background: '#2ecc71', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Authorize</button>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
