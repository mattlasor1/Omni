import { useEffect, useMemo, useRef, useState } from "react";
import Head from "next/head";

const apiBase = "http://127.0.0.1:8000/api/v1";

const baseInputStyle = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid #3b4657",
  backgroundColor: "#111827",
  color: "#e5e7eb",
  boxSizing: "border-box",
};

export default function TwinExecutionInterface() {
  const [ask, setAsk] = useState("");
  const [executionBlocks, setExecutionBlocks] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [subconsciousState, setSubconsciousState] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [profileState, setProfileState] = useState(null);
  const [planState, setPlanState] = useState(null);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonContent, setLessonContent] = useState("");
  const [lessonTags, setLessonTags] = useState("sql_modeling, orchestration");
  const [workspacePath, setWorkspacePath] = useState("");
  const [workspaceReport, setWorkspaceReport] = useState(null);
  const [workspaceBusy, setWorkspaceBusy] = useState(false);
  const [artifactPath, setArtifactPath] = useState("");
  const [artifactReview, setArtifactReview] = useState(null);
  const [taskEvaluation, setTaskEvaluation] = useState(null);
  const [skillBusy, setSkillBusy] = useState(false);
  const blocksEndRef = useRef(null);

  const readiness = profileState?.evaluation?.readiness_score ?? 0;
  const selfReview = profileState?.self_review ?? null;
  const remediationItems = profileState?.remediation_queue ?? [];
  const activeTaskEvaluation = taskEvaluation || profileState?.task_evaluation || null;

  const activeCompetencies = useMemo(
    () => profileState?.profile?.competencies || [],
    [profileState]
  );

  useEffect(() => {
    const eventSource = new EventSource(`${apiBase}/subconscious/stream`);
    eventSource.onmessage = (event) => {
      try {
        setSubconsciousState(JSON.parse(event.data));
      } catch (error) {
        console.error("Error parsing subconscious state", error);
      }
    };
    return () => eventSource.close();
  }, []);

  useEffect(() => {
    refreshTraining();
    fetch(`${apiBase}/training/templates`)
      .then((res) => res.json())
      .then((data) => setTemplates(data.templates || []))
      .catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    blocksEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [executionBlocks]);

  const refreshTraining = async () => {
    try {
      const [profileRes, planRes] = await Promise.all([
        fetch(`${apiBase}/training/profile`),
        fetch(`${apiBase}/training/plan`),
      ]);
      const profileData = await profileRes.json();
      setProfileState(profileData);
      setWorkspaceReport(profileData.workspace || null);
      setTaskEvaluation(profileData.task_evaluation || null);
      setArtifactReview((profileData.artifact_reviews || []).slice(-1)[0] || null);
      setPlanState(await planRes.json());
    } catch (error) {
      console.error("Training refresh failed", error);
    }
  };

  const bootstrapDataEngineer = async () => {
    await fetch(`${apiBase}/training/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        template_id: "data_engineer",
        display_name: "My Data Engineer Twin",
        goals: [
          "Help debug warehouse issues",
          "Improve DAG and dbt design decisions",
          "Produce stronger runbooks and reviews",
        ],
      }),
    });
    await refreshTraining();
  };

  const addLesson = async () => {
    if (!lessonTitle.trim() || !lessonContent.trim()) {
      return;
    }
    await fetch(`${apiBase}/training/lesson`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: lessonTitle,
        content: lessonContent,
        skill_tags: lessonTags.split(",").map((tag) => tag.trim()).filter(Boolean),
        lesson_type: "runbook",
        source_id: "frontend_training_console",
      }),
    });
    setLessonTitle("");
    setLessonContent("");
    await refreshTraining();
  };

  const analyzeWorkspace = async (importMode = false) => {
    if (!workspacePath.trim()) {
      return;
    }
    setWorkspaceBusy(true);
    try {
      const endpoint = importMode ? "import" : "analyze";
      const res = await fetch(`${apiBase}/training/workspace/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: workspacePath, max_files: 200, lesson_limit: 20 }),
      });
      const data = await res.json();
      setWorkspaceReport(data.report || null);
      if (importMode) {
        await refreshTraining();
      }
    } catch (error) {
      console.error("Workspace analysis failed", error);
    } finally {
      setWorkspaceBusy(false);
    }
  };

  const reviewArtifact = async () => {
    if (!artifactPath.trim()) {
      return;
    }
    setSkillBusy(true);
    try {
      const res = await fetch(`${apiBase}/training/artifact/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: artifactPath }),
      });
      const data = await res.json();
      setArtifactReview(data.review || null);
      await refreshTraining();
    } catch (error) {
      console.error("Artifact review failed", error);
    } finally {
      setSkillBusy(false);
    }
  };

  const runTaskEvaluation = async () => {
    setSkillBusy(true);
    try {
      const res = await fetch(`${apiBase}/training/evals/run`, { method: "POST" });
      const data = await res.json();
      setTaskEvaluation(data.evaluation || null);
      await refreshTraining();
    } catch (error) {
      console.error("Task evaluation failed", error);
    } finally {
      setSkillBusy(false);
    }
  };

  const sendAsk = async () => {
    if (!ask.trim() || isProcessing) {
      return;
    }
    setIsProcessing(true);
    const blockId = Date.now().toString();
    const block = {
      id: blockId,
      ask,
      status: "Initializing...",
      response: "",
      process_used: "",
      context: [],
      action_decided: null,
      action_result: null,
      mcts_prediction: null,
      paused: false,
      completed: false,
    };
    setExecutionBlocks((prev) => [...prev, block]);
    setAsk("");

    try {
      const response = await fetch(`${apiBase}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: block.ask, execute_action: true }),
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (!line.startsWith("data: ")) {
            continue;
          }
          try {
            const data = JSON.parse(line.slice(6));
            setExecutionBlocks((prevBlocks) =>
              prevBlocks.map((entry) => {
                if (entry.id !== blockId) {
                  return entry;
                }
                const next = { ...entry };
                if (data.event === "status") {
                  next.status = data.data;
                } else if (data.event === "context") {
                  next.context = data.data;
                } else if (data.event === "response") {
                  next.response = data.data;
                  next.process_used = data.process_used;
                } else if (data.event === "action_decided") {
                  next.action_decided = data.data;
                } else if (data.event === "mcts_prediction") {
                  next.mcts_prediction = data.data;
                } else if (data.event === "action_result") {
                  next.action_result = data.data;
                } else if (data.event === "action_paused") {
                  next.paused = true;
                  next.pending_action_id = data.action_id;
                  next.action_result = data.data;
                } else if (data.event === "action_vetoed") {
                  next.action_result = `VETOED: ${data.data}`;
                } else if (data.event === "complete") {
                  next.completed = true;
                  next.status = "Completed";
                }
                return next;
              })
            );
          } catch (error) {
            console.error("SSE parse error", error);
          }
        }
      }
    } catch (error) {
      console.error("Stream error", error);
    } finally {
      setIsProcessing(false);
      refreshTraining();
    }
  };

  const getStressColor = (stress) => {
    if (stress < 0.4) return "#22c55e";
    if (stress < 0.75) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#0b1120", color: "#e5e7eb", fontFamily: "Inter, Segoe UI, sans-serif" }}>
      <Head>
        <title>OmniTwin Offline Workbench</title>
      </Head>

      <div style={{ position: "sticky", top: 0, zIndex: 20, backgroundColor: "rgba(11,17,32,0.92)", borderBottom: "1px solid #1f2937" }}>
        <div style={{ maxWidth: "1380px", margin: "0 auto", padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "20px" }}>
          <div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>OmniTwin Offline Workbench</div>
            <div style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
              {profileState?.profile ? `${profileState.profile.display_name} active` : "No profession profile configured yet"}
            </div>
          </div>
          {subconsciousState ? (
            <div style={{ display: "flex", gap: "18px", alignItems: "center", fontSize: "0.85rem", color: "#cbd5e1" }}>
              <span>{subconsciousState.status}</span>
              <span>Peers {subconsciousState.peers}</span>
              <span>CPU {subconsciousState.cpu.toFixed(1)}%</span>
              <span>RAM {subconsciousState.ram.toFixed(1)}%</span>
              <div style={{ width: "84px", height: "8px", borderRadius: "999px", backgroundColor: "#1f2937", overflow: "hidden" }}>
                <div style={{ width: `${Math.min(100, subconsciousState.hw_stress * 100)}%`, height: "100%", backgroundColor: getStressColor(subconsciousState.hw_stress) }} />
              </div>
            </div>
          ) : (
            <div style={{ color: "#94a3b8", fontSize: "0.9rem" }}>Starting local daemon...</div>
          )}
        </div>
      </div>

      <div style={{ maxWidth: "1380px", margin: "0 auto", padding: "20px", display: "grid", gridTemplateColumns: "360px minmax(0, 1fr)", gap: "20px" }}>
        <aside style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "8px" }}>Twin Training</div>
            {!profileState?.profile ? (
              <>
                <p style={{ color: "#cbd5e1", fontSize: "0.92rem", lineHeight: 1.5 }}>
                  Start with a profession template so Omni learns in the shape of real work, not generic memory.
                </p>
                <button onClick={bootstrapDataEngineer} style={{ width: "100%", padding: "12px", borderRadius: "10px", backgroundColor: "#2563eb", color: "#fff", border: "none", cursor: "pointer", fontWeight: 600 }}>
                  Create Data Engineer Twin
                </button>
                <div style={{ marginTop: "10px", color: "#64748b", fontSize: "0.82rem" }}>
                  Available templates: {templates.map((template) => template.label).join(", ")}
                </div>
              </>
            ) : (
              <>
                <div style={{ fontSize: "1rem", fontWeight: 600 }}>{profileState.profile.display_name}</div>
                <div style={{ color: "#cbd5e1", fontSize: "0.9rem", lineHeight: 1.5 }}>{profileState.profile.summary}</div>
                <div style={{ marginTop: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", color: "#94a3b8", marginBottom: "6px" }}>
                    <span>Readiness</span>
                    <span>{Math.round(readiness * 100)}%</span>
                  </div>
                  <div style={{ height: "10px", backgroundColor: "#1f2937", borderRadius: "999px", overflow: "hidden" }}>
                    <div style={{ width: `${Math.round(readiness * 100)}%`, height: "100%", backgroundColor: readiness >= 0.8 ? "#22c55e" : "#38bdf8" }} />
                  </div>
                </div>
                <button onClick={refreshTraining} style={{ marginTop: "12px", width: "100%", padding: "10px", borderRadius: "10px", backgroundColor: "#1d4ed8", color: "#fff", border: "none", cursor: "pointer" }}>
                  Refresh Training Status
                </button>
              </>
            )}
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Competency Coverage</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {activeCompetencies.length === 0 ? (
                <div style={{ color: "#64748b", fontSize: "0.9rem" }}>No competencies yet.</div>
              ) : (
                activeCompetencies.map((competency) => {
                  const pct = Math.min(100, Math.round((competency.evidence_ids.length / competency.target_evidence) * 100));
                  return (
                    <div key={competency.name}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.84rem", marginBottom: "4px" }}>
                        <span>{competency.label}</span>
                        <span>{competency.evidence_ids.length}/{competency.target_evidence}</span>
                      </div>
                      <div style={{ height: "8px", backgroundColor: "#1f2937", borderRadius: "999px", overflow: "hidden" }}>
                        <div style={{ width: `${pct}%`, height: "100%", backgroundColor: "#22c55e" }} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Add Lesson</div>
            <input value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} placeholder="Lesson title" style={baseInputStyle} />
            <textarea value={lessonContent} onChange={(e) => setLessonContent(e.target.value)} placeholder="Capture a rule, runbook, failure mode, or preferred pattern." style={{ ...baseInputStyle, minHeight: "110px", marginTop: "10px", resize: "vertical" }} />
            <input value={lessonTags} onChange={(e) => setLessonTags(e.target.value)} placeholder="skill tags" style={{ ...baseInputStyle, marginTop: "10px" }} />
            <button onClick={addLesson} style={{ marginTop: "12px", width: "100%", padding: "12px", borderRadius: "10px", backgroundColor: "#0f766e", color: "#fff", border: "none", cursor: "pointer", fontWeight: 600 }}>
              Store Lesson
            </button>
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Import Workspace</div>
            <input
              value={workspacePath}
              onChange={(e) => setWorkspacePath(e.target.value)}
              placeholder="C:\\work\\analytics or /repos/project"
              style={baseInputStyle}
            />
            <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
              <button
                onClick={() => analyzeWorkspace(false)}
                disabled={workspaceBusy || !workspacePath.trim()}
                style={{ flex: 1, padding: "12px", borderRadius: "10px", backgroundColor: workspaceBusy ? "#334155" : "#1d4ed8", color: "#fff", border: "none", cursor: workspaceBusy ? "not-allowed" : "pointer", fontWeight: 600 }}
              >
                Analyze
              </button>
              <button
                onClick={() => analyzeWorkspace(true)}
                disabled={workspaceBusy || !workspacePath.trim()}
                style={{ flex: 1, padding: "12px", borderRadius: "10px", backgroundColor: workspaceBusy ? "#334155" : "#7c3aed", color: "#fff", border: "none", cursor: workspaceBusy ? "not-allowed" : "pointer", fontWeight: 600 }}
              >
                Import
              </button>
            </div>
            <div style={{ marginTop: "10px", color: "#64748b", fontSize: "0.82rem", lineHeight: 1.5 }}>
              Point Omni at a local repo, runbook folder, or analytics project to extract profession-specific lessons automatically.
            </div>
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Skill Pack</div>
            <input
              value={artifactPath}
              onChange={(e) => setArtifactPath(e.target.value)}
              placeholder="models/orders.sql"
              style={baseInputStyle}
            />
            <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
              <button
                onClick={reviewArtifact}
                disabled={skillBusy || !artifactPath.trim()}
                style={{ flex: 1, padding: "12px", borderRadius: "10px", backgroundColor: skillBusy || !artifactPath.trim() ? "#334155" : "#0f766e", color: "#fff", border: "none", cursor: skillBusy || !artifactPath.trim() ? "not-allowed" : "pointer", fontWeight: 600 }}
              >
                Review File
              </button>
              <button
                onClick={runTaskEvaluation}
                disabled={skillBusy}
                style={{ flex: 1, padding: "12px", borderRadius: "10px", backgroundColor: skillBusy ? "#334155" : "#7c3aed", color: "#fff", border: "none", cursor: skillBusy ? "not-allowed" : "pointer", fontWeight: 600 }}
              >
                Run Eval
              </button>
            </div>
            {activeTaskEvaluation && (
              <div style={{ marginTop: "12px", color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>
                Task score {Math.round(activeTaskEvaluation.overall_score || 0)} | {activeTaskEvaluation.status}
              </div>
            )}
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Next Best Training Moves</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", color: "#cbd5e1", fontSize: "0.9rem" }}>
              {(planState?.next_steps || profileState?.plan?.next_steps || []).map((step) => (
                <div key={step} style={{ padding: "10px", backgroundColor: "#0b1220", borderRadius: "8px" }}>{step}</div>
              ))}
            </div>
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Continuous Self-Review</div>
            {!selfReview ? (
              <div style={{ color: "#64748b", fontSize: "0.9rem" }}>
                Self-review will appear after the twin has enough profile or workspace context to evaluate itself.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ color: "#e5e7eb", fontSize: "0.92rem" }}>
                  Readiness {Math.round((selfReview.readiness_score || 0) * 100)}% with {selfReview.recent_interaction_count || 0} recent interaction(s).
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.82rem" }}>
                  Trigger: {selfReview.trigger} {typeof selfReview.trend_delta === "number" ? `| Delta ${selfReview.trend_delta >= 0 ? "+" : ""}${selfReview.trend_delta.toFixed(2)}` : ""}
                </div>
                {(selfReview.generated_reflections || []).length > 0 && (
                  <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>
                    New syntheses: {(selfReview.generated_reflections || []).map((item) => item.title).join(", ")}
                  </div>
                )}
                {(selfReview.strengths || []).length > 0 && (
                  <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>
                    Strengths: {selfReview.strengths.join(", ")}
                  </div>
                )}
              </div>
            )}
          </section>

          <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "18px" }}>
            <div style={{ fontSize: "0.85rem", color: "#93c5fd", marginBottom: "10px" }}>Gap Queue</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", color: "#cbd5e1", fontSize: "0.9rem" }}>
              {remediationItems.length === 0 ? (
                <div style={{ color: "#64748b" }}>No open remediation items.</div>
              ) : (
                remediationItems.slice(0, 4).map((item) => (
                  <div key={item.id || item.recommendation} style={{ padding: "10px", backgroundColor: "#0b1220", borderRadius: "8px" }}>
                    <div style={{ fontWeight: 600, fontSize: "0.86rem", marginBottom: "4px" }}>{item.title}</div>
                    <div style={{ color: "#cbd5e1", fontSize: "0.84rem", lineHeight: 1.5 }}>{item.recommendation}</div>
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>

        <main style={{ display: "flex", flexDirection: "column", gap: "16px", minWidth: 0 }}>
          {executionBlocks.length === 0 && (
            <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "24px" }}>
              <div style={{ fontSize: "1.5rem", fontWeight: 600, marginBottom: "10px" }}>Train locally. Query locally. Improve locally.</div>
              <div style={{ color: "#cbd5e1", lineHeight: 1.6 }}>
                Omni now keeps a profession profile, accepts explicit lessons, and answers from the local memory it has actually earned.
              </div>
            </section>
          )}

          {workspaceReport && (
            <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", marginBottom: "12px", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 600 }}>{workspaceReport.workspace_name || "Workspace Snapshot"}</div>
                  <div style={{ color: "#94a3b8", fontSize: "0.85rem" }}>{workspaceReport.workspace_path}</div>
                </div>
                <div style={{ color: "#cbd5e1", fontSize: "0.85rem" }}>
                  {workspaceReport.imported_lessons ? `${workspaceReport.imported_lessons} lesson(s) imported` : `${workspaceReport.selected_files || 0} files analyzed`}
                </div>
              </div>
              <div style={{ color: "#e5e7eb", lineHeight: 1.6, marginBottom: "12px" }}>{workspaceReport.summary}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "14px" }}>
                {(workspaceReport.frameworks || []).map((framework) => (
                  <span key={framework} style={{ padding: "6px 10px", borderRadius: "999px", backgroundColor: "#0b1220", color: "#93c5fd", fontSize: "0.8rem" }}>
                    {framework}
                  </span>
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "14px" }}>
                <div style={{ backgroundColor: "#0b1220", borderRadius: "8px", padding: "14px" }}>
                  <div style={{ color: "#93c5fd", fontSize: "0.78rem", textTransform: "uppercase", marginBottom: "8px" }}>Top Artifacts</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {(workspaceReport.artifacts || []).slice(0, 4).map((artifact) => (
                      <div key={artifact.path}>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{artifact.path}</div>
                        <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>{artifact.summary}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ backgroundColor: "#0b1220", borderRadius: "8px", padding: "14px" }}>
                  <div style={{ color: "#93c5fd", fontSize: "0.78rem", textTransform: "uppercase", marginBottom: "8px" }}>Evaluation Scenarios</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {(workspaceReport.evaluation_scenarios || []).map((scenario) => (
                      <div key={scenario.name}>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{scenario.name}</div>
                        <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>{scenario.goal}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "8px" }}>
                {(workspaceReport.recommended_next_steps || []).slice(0, 3).map((step) => (
                  <div key={step} style={{ padding: "10px", backgroundColor: "#0b1220", borderRadius: "8px", color: "#cbd5e1", fontSize: "0.9rem" }}>
                    {step}
                  </div>
                ))}
              </div>
            </section>
          )}

          {artifactReview && (
            <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", marginBottom: "12px", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 600 }}>{artifactReview.path}</div>
                  <div style={{ color: "#94a3b8", fontSize: "0.85rem" }}>{artifactReview.artifact_type} | {artifactReview.grade}</div>
                </div>
                <div style={{ color: "#e5e7eb", fontSize: "1.4rem", fontWeight: 700 }}>{Math.round(artifactReview.score || 0)}</div>
              </div>
              <div style={{ color: "#e5e7eb", lineHeight: 1.6, marginBottom: "12px" }}>{artifactReview.summary}</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {(artifactReview.findings || []).slice(0, 4).map((finding) => (
                  <div key={`${finding.severity}-${finding.title}`} style={{ padding: "12px", backgroundColor: "#0b1220", borderRadius: "8px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", marginBottom: "4px" }}>
                      <span style={{ fontWeight: 600 }}>{finding.title}</span>
                      <span style={{ color: finding.severity === "high" || finding.severity === "critical" ? "#f97316" : "#93c5fd", fontSize: "0.82rem" }}>{finding.severity}</span>
                    </div>
                    <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>{finding.recommendation}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {activeTaskEvaluation && (
            <section style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", marginBottom: "12px", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 600 }}>Task Evaluation</div>
                  <div style={{ color: "#94a3b8", fontSize: "0.85rem" }}>{activeTaskEvaluation.status}</div>
                </div>
                <div style={{ color: "#e5e7eb", fontSize: "1.4rem", fontWeight: 700 }}>{Math.round(activeTaskEvaluation.overall_score || 0)}</div>
              </div>
              <div style={{ color: "#e5e7eb", lineHeight: 1.6, marginBottom: "12px" }}>{activeTaskEvaluation.summary}</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "12px" }}>
                {(activeTaskEvaluation.tasks || []).map((task) => (
                  <div key={task.name} style={{ backgroundColor: "#0b1220", borderRadius: "8px", padding: "14px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", marginBottom: "6px" }}>
                      <span style={{ fontWeight: 600 }}>{task.name}</span>
                      <span style={{ color: task.status === "ready" ? "#22c55e" : "#f59e0b", fontSize: "0.82rem" }}>{task.status}</span>
                    </div>
                    <div style={{ color: "#cbd5e1", fontSize: "0.86rem", lineHeight: 1.5 }}>{task.next_step}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {executionBlocks.map((block) => (
            <section key={block.id} style={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "20px" }}>
              <div style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "8px" }}>{block.ask}</div>
              <div style={{ color: "#60a5fa", fontSize: "0.88rem", marginBottom: "14px" }}>{block.status}</div>
              {block.response && (
                <div style={{ backgroundColor: "#0b1220", borderRadius: "8px", padding: "14px", marginBottom: "12px" }}>
                  <div style={{ color: "#93c5fd", fontSize: "0.78rem", textTransform: "uppercase", marginBottom: "6px" }}>
                    Response {block.process_used ? `(${block.process_used})` : ""}
                  </div>
                  <div style={{ color: "#e5e7eb", lineHeight: 1.6 }}>{block.response}</div>
                </div>
              )}
              {block.context?.length > 0 && (
                <div style={{ backgroundColor: "#0b1220", borderRadius: "8px", padding: "14px", marginBottom: "12px" }}>
                  <div style={{ color: "#fbbf24", fontSize: "0.78rem", textTransform: "uppercase", marginBottom: "6px" }}>Local Context</div>
                  <ul style={{ margin: 0, paddingLeft: "18px", color: "#cbd5e1", lineHeight: 1.6 }}>
                    {block.context.map((item, index) => <li key={`${block.id}-${index}`}>{item}</li>)}
                  </ul>
                </div>
              )}
              {block.action_decided && (
                <div style={{ color: "#cbd5e1", marginBottom: "8px" }}>
                  <strong>Action:</strong> {block.action_decided.action} <span style={{ color: "#94a3b8" }}>({block.action_decided.reason})</span>
                </div>
              )}
              {block.mcts_prediction && (
                <div style={{ color: "#cbd5e1", marginBottom: "8px" }}>
                  <strong>Simulation:</strong> {block.mcts_prediction}
                </div>
              )}
              {block.action_result && (
                <div style={{ color: "#cbd5e1" }}>
                  <strong>Execution:</strong> {block.action_result}
                </div>
              )}
            </section>
          ))}

          <div ref={blocksEndRef} />
        </main>
      </div>

      <div style={{ position: "fixed", left: 0, right: 0, bottom: 0, borderTop: "1px solid #1f2937", backgroundColor: "rgba(11,17,32,0.96)", padding: "16px 20px" }}>
        <div style={{ maxWidth: "1380px", margin: "0 auto", display: "flex", gap: "10px" }}>
          <input
            type="text"
            value={ask}
            onChange={(e) => setAsk(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendAsk()}
            placeholder={isProcessing ? "Omni is working..." : "Ask Omni to reason from your local training and memory..."}
            disabled={isProcessing}
            style={{ ...baseInputStyle, flex: 1 }}
          />
          <button
            onClick={sendAsk}
            disabled={isProcessing || !ask.trim()}
            style={{
              minWidth: "120px",
              borderRadius: "10px",
              border: "none",
              backgroundColor: isProcessing || !ask.trim() ? "#334155" : "#2563eb",
              color: "#fff",
              fontWeight: 600,
              cursor: isProcessing || !ask.trim() ? "not-allowed" : "pointer",
            }}
          >
            Run
          </button>
        </div>
      </div>
    </div>
  );
}
