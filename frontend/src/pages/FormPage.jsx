import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Users,
  Zap,
  Wallet,
  ArrowRight,
  X,
  Home,
  Calendar,
  Flame,
  FileText,
} from "lucide-react";

const leads = [
  {
    id: 1,
    name: "Markus Weber",
    postal_code: "74238",
    city: "Krautheim",
    product_interest: "Heat pump",
    household_size: 4,
    house_type: "Detached",
    build_year: 1985,
    roof_orientation: "South",
    electricity_kwh_year: 4500,
    heating_type: "Gas",
    monthly_energy_bill_eur: 180,
    existing_assets: "None",
    financial_profile: "Mid-income, open to financing",
    notes: "Concerned about rising gas prices",
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
  const [leadDialogOpen, setLeadDialogOpen] = useState(false);

  const formatProduct = (value) => {
    if (!value) return "—";

    return value
      .replace(/_/g, " ")
      .split(" ")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  };

  const getLeadLocation = (lead) => lead.city || lead.area || "—";

  const getLeadPostalCode = (lead) => lead.postal_code || lead.postcode || "—";

  const getLeadUsage = (lead) =>
    lead.electricity_kwh_year || lead.annual_consumption_kwh || "—";

  const getLeadBudget = (lead) =>
    lead.financial_profile || lead.budget_band || "—";

  const getLeadNote = (lead) => lead.notes || lead.customer_goal || "—";

  const handleLeadOpen = (leadId) => {
    setLeadDialogOpen(false);
    navigate(`/lead/${leadId}`);
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
                Select a lead card to open the customer details page.
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="dashboard-main-layout single-column-layout"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.08 }}
        >
          <div className="dashboard-left full-width-section">
            <div className="dashboard-section-header">
              <h2>Available Leads</h2>
              <span>{leads.length} profiles</span>
            </div>

            <div className="dashboard-cards-grid horizontal-cards-grid">
              {leads.map((lead) => (
                <motion.button
                  key={lead.id}
                  className="lead-dashboard-card lead-dashboard-card-horizontal"
                  whileHover={{ y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => navigate(`/lead/${lead.id}`)}
                >
                  <div className="lead-card-top">
                    <div>
                      <h3>{lead.name}</h3>
                      <p>{formatProduct(lead.product_interest)}</p>
                    </div>
                    <span className="lead-status-badge">Active Lead</span>
                  </div>

                  <div className="lead-card-body horizontal-card-body">
                    <div className="lead-card-row">
                      <span>
                        <MapPin size={15} /> City
                      </span>
                      <strong>{getLeadLocation(lead)}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <MapPin size={15} /> Postal Code
                      </span>
                      <strong>{getLeadPostalCode(lead)}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Users size={15} /> Household
                      </span>
                      <strong>{lead.household_size || "—"} people</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Zap size={15} /> Electricity
                      </span>
                      <strong>{getLeadUsage(lead)} kWh</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Wallet size={15} /> Budget
                      </span>
                      <strong>{getLeadBudget(lead)}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Home size={15} /> House Type
                      </span>
                      <strong>{lead.house_type || "—"}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Calendar size={15} /> Build Year
                      </span>
                      <strong>{lead.build_year || "—"}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <MapPin size={15} /> Roof Orientation
                      </span>
                      <strong>{lead.roof_orientation || "—"}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Flame size={15} /> Heating Type
                      </span>
                      <strong>{lead.heating_type || "—"}</strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <Wallet size={15} /> Monthly Bill
                      </span>
                      <strong>
                        {lead.monthly_energy_bill_eur
                          ? `€${lead.monthly_energy_bill_eur}`
                          : "—"}
                      </strong>
                    </div>

                    <div className="lead-card-row">
                      <span>
                        <FileText size={15} /> Existing Assets
                      </span>
                      <strong>{lead.existing_assets || "—"}</strong>
                    </div>

                    <div className="lead-card-row lead-card-row-full">
                      <span>
                        <FileText size={15} /> Notes
                      </span>
                      <strong>{getLeadNote(lead)}</strong>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>

            <div className="dashboard-bottom-action">
              <button
                className="primary-btn"
                onClick={() => navigate("/chat")}
              >
                Open Lead Selector
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {leadDialogOpen && (
          <motion.div
            className="lead-dialog-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLeadDialogOpen(false)}
          >
            <motion.div
              className="lead-dialog-box"
              initial={{ opacity: 0, y: 20, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 14, scale: 0.96 }}
              transition={{ duration: 0.25 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="lead-dialog-header">
                <div>
                  <p className="dashboard-kicker">Choose Lead</p>
                  <h3>Select a customer profile</h3>
                </div>

                <button
                  className="lead-dialog-close-btn"
                  onClick={() => setLeadDialogOpen(false)}
                >
                  <X size={18} />
                </button>
              </div>

              <div className="lead-dialog-list">
                {leads.map((lead) => (
                  <motion.button
                    key={lead.id}
                    className="lead-dialog-card"
                    whileHover={{ y: -3 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleLeadOpen(lead.id)}
                  >
                    <div className="lead-dialog-card-top">
                      <div>
                        <h4>{lead.name}</h4>
                        <p>{formatProduct(lead.product_interest)}</p>
                      </div>
                      <ArrowRight size={18} />
                    </div>

                    <div className="lead-dialog-card-body">
                      <div className="lead-card-row">
                        <span>
                          <MapPin size={15} /> City
                        </span>
                        <strong>{getLeadLocation(lead)}</strong>
                      </div>

                      <div className="lead-card-row">
                        <span>
                          <Users size={15} /> Household
                        </span>
                        <strong>{lead.household_size || "—"} people</strong>
                      </div>

                      <div className="lead-card-row">
                        <span>
                          <Zap size={15} /> Usage
                        </span>
                        <strong>{getLeadUsage(lead)} kWh</strong>
                      </div>

                      <div className="lead-card-row">
                        <span>
                          <Wallet size={15} /> Budget
                        </span>
                        <strong>{getLeadBudget(lead)}</strong>
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}