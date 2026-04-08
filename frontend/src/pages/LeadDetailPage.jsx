import { useParams, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, MessageCircle, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const leads = {
  1: {
    name: "Lukas Schneider",
    postcode: "68169",
    area: "Mannheim",
    household: 3,
  },
  2: {
    name: "Emma Fischer",
    postcode: "69115",
    area: "Heidelberg",
    household: 2,
  },
  3: {
    name: "Noah Weber",
    postcode: "70173",
    area: "Stuttgart",
    household: 4,
  },
};

export default function LeadDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const lead = leads[id];

  const [chatOpen, setChatOpen] = useState(false);

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
      </div>

      {/* CHAT */}
      <button
        className="dashboard-chat-fab"
        onClick={() => setChatOpen(true)}
      >
        <MessageCircle size={22} />
      </button>

      <AnimatePresence>
        {chatOpen && (
          <motion.div
            className="dashboard-chat-panel"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="chat-header">
              <h3>AI Assistant</h3>
              <button onClick={() => setChatOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="chat-body">
              <p>Helping with {lead.name}'s case...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}