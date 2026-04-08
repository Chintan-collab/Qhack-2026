import { useParams, useNavigate } from "react-router-dom";
import { useState, useCallback } from "react";
import { ArrowLeft, MessageCircle, X, Send, Mic, MicOff, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const leads = {
  1: {
    name: "Lukas Schneider",
    postcode: "68169",
    area: "Mannheim",
    household: 3,
    product_interest: "solar_battery",
    budget_band: "medium",
    annual_consumption_kwh: 4200,
    customer_goal: "Reduce monthly bills and improve energy independence",
  },
  2: {
    name: "Emma Fischer",
    postcode: "69115",
    area: "Heidelberg",
    household: 2,
    product_interest: "heat_pump",
    budget_band: "high",
    annual_consumption_kwh: 2800,
    customer_goal: "Upgrade heating system for long-term savings",
  },
  3: {
    name: "Noah Weber",
    postcode: "70173",
    area: "Stuttgart",
    household: 4,
    product_interest: "wallbox",
    budget_band: "medium",
    annual_consumption_kwh: 5100,
    customer_goal: "Prepare home charging setup for EV usage",
  },
};

export default function LeadDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const lead = leads[id];

  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [projectId, setProjectId] = useState(null);

  // Create a project from lead data so the agent knows what's already collected
  const ensureProject = useCallback(async () => {
    if (projectId) return projectId;

    const res = await fetch("/api/v1/projects/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: lead.name,
        customer_name: lead.name,
        postal_code: lead.postcode,
        city: lead.area,
        product_interest: lead.product_interest?.replace(/_/g, " + "),
        household_size: lead.household,
        electricity_kwh_year: lead.annual_consumption_kwh,
        financial_profile: lead.budget_band,
        notes: lead.customer_goal,
      }),
    });
    const project = await res.json();
    setProjectId(project.id);
    return project.id;
  }, [projectId, lead]);

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || loading) return;

      const userMsg = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const pid = await ensureProject();

        const res = await fetch("/api/v1/chat/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            project_id: pid,
            message: text,
          }),
        });
        const data = await res.json();

        if (!conversationId) {
          setConversationId(data.conversation_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.message,
            agent: data.metadata?.agent_name,
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Sorry, something went wrong." },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading, conversationId, ensureProject],
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="lead-detail-page">
      <button className="back-link-btn" onClick={() => navigate("/form")}>
        <ArrowLeft size={18} /> Back
      </button>

      <h1>{lead.name}</h1>

      <div className="lead-detail-card">
        <p><strong>Area:</strong> {lead.area}</p>
        <p><strong>Postcode:</strong> {lead.postcode}</p>
        <p><strong>Household:</strong> {lead.household}</p>
        <p><strong>Product:</strong> {lead.product_interest}</p>
        <p><strong>Consumption:</strong> {lead.annual_consumption_kwh} kWh/year</p>
        <p><strong>Budget:</strong> {lead.budget_band}</p>
        <p><strong>Goal:</strong> {lead.customer_goal}</p>
      </div>

      <div style={{ display: "flex", gap: "12px", marginTop: "20px" }}>
        <button
          className="primary-btn"
          onClick={() => navigate(`/chat`)}
        >
          Open Full Chat
        </button>
        <button
          className="secondary-btn"
          onClick={() => navigate("/report")}
        >
          View Report
        </button>
      </div>

      {/* Chat FAB */}
      <button
        className="dashboard-chat-fab"
        onClick={() => setChatOpen(true)}
      >
        <MessageCircle size={22} />
      </button>

      <AnimatePresence>
        {chatOpen && (
          <motion.div
            className="dashboard-chat-modal"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="dashboard-chat-box"
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 14, scale: 0.98 }}
              style={{ maxWidth: "480px", maxHeight: "600px", display: "flex", flexDirection: "column" }}
            >
              <div className="dashboard-chat-header">
                <div>
                  <h3>AI Sales Agent</h3>
                  <p>Helping with {lead.name}'s case</p>
                </div>
                <button className="chatbot-close-btn" onClick={() => setChatOpen(false)}>
                  <X size={18} />
                </button>
              </div>

              {/* Messages */}
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                {messages.length === 0 && (
                  <p style={{ color: "#94a3b8", fontSize: "0.9rem", textAlign: "center", marginTop: "40px" }}>
                    Ask me anything about {lead.name}'s case — sales strategy, product recommendations, or how to handle objections.
                  </p>
                )}

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "85%",
                      padding: "10px 14px",
                      borderRadius: "14px",
                      fontSize: "0.9rem",
                      lineHeight: "1.6",
                      background:
                        msg.role === "user"
                          ? "linear-gradient(135deg, #2563eb, #14b8a6)"
                          : "rgba(255,255,255,0.08)",
                      color: "#fff",
                    }}
                  >
                    {msg.agent && (
                      <div style={{ fontSize: "0.7rem", color: "#93c5fd", marginBottom: "4px" }}>
                        {msg.agent}
                      </div>
                    )}
                    {msg.content}
                  </div>
                ))}

                {loading && (
                  <div style={{ alignSelf: "flex-start", color: "#94a3b8", fontSize: "0.85rem" }}>
                    <Loader2 size={16} style={{ display: "inline", animation: "spin 1s linear infinite" }} />
                    {" "}Thinking...
                  </div>
                )}
              </div>

              {/* Input */}
              <form
                onSubmit={handleSubmit}
                style={{
                  display: "flex",
                  gap: "8px",
                  padding: "12px 16px",
                  borderTop: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about this lead..."
                  disabled={loading}
                  style={{
                    flex: 1,
                    background: "rgba(255,255,255,0.07)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    padding: "10px 14px",
                    color: "#fff",
                    fontSize: "0.9rem",
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="primary-btn"
                  style={{ padding: "10px 16px", borderRadius: "12px" }}
                >
                  <Send size={16} />
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
