import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Users,
  Zap,
  Wallet,
  BatteryCharging,
  MessageCircle,
  X,
  ArrowRight,
  Target,
} from "lucide-react";

const leads = [
  {
    id: 1,
    name: "Lukas Schneider",
    area: "Mannheim",
    postcode: "68169",
    household_size: 3,
    annual_consumption_kwh: 4200,
    budget_band: "medium",
    product_interest: "solar_battery",
    customer_goal: "Reduce monthly bills and improve energy independence",
  },
  {
    id: 2,
    name: "Emma Fischer",
    area: "Heidelberg",
    postcode: "69115",
    household_size: 2,
    annual_consumption_kwh: 2800,
    budget_band: "high",
    product_interest: "heat_pump",
    customer_goal: "Upgrade heating system for long-term savings",
  },
  {
    id: 3,
    name: "Noah Weber",
    area: "Stuttgart",
    postcode: "70173",
    household_size: 4,
    annual_consumption_kwh: 5100,
    budget_band: "medium",
    product_interest: "wallbox",
    customer_goal: "Prepare home charging setup for EV usage",
  },
];

export default function FormPage() {
  const navigate = useNavigate();
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(leads[0]);

  const formatProduct = (value) => {
    if (!value) return "—";
    return value
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" + ");
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-bg-glow dashboard-glow-1"></div>
      <div className="dashboard-bg-glow dashboard-glow-2"></div>
      <div className="dashboard-grid-overlay"></div>

      <div className="dashboard-container">
        <motion.div
          className="dashboard-header"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="dashboard-header-left">
            <button className="back-link-btn" onClick={() => navigate("/")}>
              <ArrowLeft size={18} />
              Back
            </button>

            <div>
              <p className="dashboard-kicker">Lead Qualification Workspace</p>
              <h1>Sales Dashboard</h1>
              <p className="dashboard-subtitle">
                Select a lead and review their profile before generating a sales report.
              </p>
            </div>
          </div>

          <button
            className="primary-btn dashboard-header-btn"
            onClick={() => navigate(`/lead/${selectedLead.id}`)}
          >
            Open Lead Page
            <ArrowRight size={18} />
          </button>
        </motion.div>

        <motion.div
          className="dashboard-main-layout"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.08 }}
        >
          <div className="dashboard-left">
            <div className="dashboard-section-header">
              <h2>Available Leads</h2>
              <span>{leads.length} profiles</span>
            </div>

            <div className="dashboard-cards-grid">
              {leads.map((lead) => (
                <motion.button
                  key={lead.id}
                  className={`lead-dashboard-card ${
                    selectedLead.id === lead.id ? "lead-dashboard-card-active" : ""
                  }`}
                  whileHover={{ y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setSelectedLead(lead)}
                >
                  <div className="lead-card-top">
                    <div>
                      <h3>{lead.name}</h3>
                      <p>{formatProduct(lead.product_interest)}</p>
                    </div>
                    <span className="lead-status-badge">Active Lead</span>
                  </div>

                  <div className="lead-card-body">
                    <div className="lead-card-row">
                      <span><MapPin size={15} /> Area</span>
                      <strong>{lead.area}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span><Users size={15} /> Household</span>
                      <strong>{lead.household_size} people</strong>
                    </div>

                    <div className="lead-card-row">
                      <span><Zap size={15} /> Usage</span>
                      <strong>{lead.annual_consumption_kwh} kWh</strong>
                    </div>

                    <div className="lead-card-row">
                      <span><Wallet size={15} /> Budget</span>
                      <strong>{lead.budget_band}</strong>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>

          <div className="dashboard-right">
            <div className="lead-preview-card">
              <div className="lead-preview-header">
                <div>
                  <p className="dashboard-kicker">Selected Lead Preview</p>
                  <h2>{selectedLead.name}</h2>
                </div>
                <span className="lead-preview-tag">
                  {formatProduct(selectedLead.product_interest)}
                </span>
              </div>

              <div className="lead-preview-grid">
                <div className="lead-preview-item">
                  <span>Area</span>
                  <p>{selectedLead.area}</p>
                </div>

                <div className="lead-preview-item">
                  <span>Postcode</span>
                  <p>{selectedLead.postcode}</p>
                </div>

                <div className="lead-preview-item">
                  <span>Household Size</span>
                  <p>{selectedLead.household_size}</p>
                </div>

                <div className="lead-preview-item">
                  <span>Consumption</span>
                  <p>{selectedLead.annual_consumption_kwh} kWh</p>
                </div>

                <div className="lead-preview-item">
                  <span>Budget Band</span>
                  <p>{selectedLead.budget_band}</p>
                </div>

                <div className="lead-preview-item">
                  <span>Product</span>
                  <p>{formatProduct(selectedLead.product_interest)}</p>
                </div>

                <div className="lead-preview-item full-width">
                  <span>Customer Goal</span>
                  <p>{selectedLead.customer_goal}</p>
                </div>
              </div>

              <div className="lead-preview-actions">
                <button
                  className="secondary-btn"
                  onClick={() => navigate(`/lead/${selectedLead.id}`)}
                >
                  View Details
                </button>

                <button
                  className="primary-btn"
                  onClick={() => navigate(`/lead/${selectedLead.id}`)}
                >
                  Continue
                  <ArrowRight size={18} />
                </button>
              </div>
            </div>

            <div className="lead-helper-card">
              <div className="lead-helper-title">
                <BatteryCharging size={18} />
                <h3>AI Assistant Hint</h3>
              </div>
              <p>
                Use the selected lead preview to review the customer profile first.
                Then open the lead page to work with chat assistance for that specific case.
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      <motion.button
        className="dashboard-chat-fab"
        onClick={() => setChatOpen(true)}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.96 }}
      >
        <MessageCircle size={22} />
      </motion.button>

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
            >
              <div className="dashboard-chat-header">
                <div>
                  <h3>Lead Navigator</h3>
                  <p>Choose a customer profile to continue</p>
                </div>

                <button
                  className="chatbot-close-btn"
                  onClick={() => setChatOpen(false)}
                >
                  <X size={18} />
                </button>
              </div>

              <div className="dashboard-chat-lead-list">
                {leads.map((lead) => (
                  <button
                    key={lead.id}
                    className="dashboard-chat-lead-item"
                    onClick={() => {
                      setChatOpen(false);
                      navigate(`/lead/${lead.id}`);
                    }}
                  >
                    <div>
                      <h4>{lead.name}</h4>
                      <p>{formatProduct(lead.product_interest)}</p>
                    </div>
                    <ArrowRight size={18} />
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}