import { useCallback, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Users,
  Zap,
  Wallet,
  Target,
  MessageCircle,
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
    name: "Anna Schneider",
    postal_code: "69120",
    city: "Heidelberg",
    product_interest: "Solar",
    household_size: 2,
    house_type: "Semi-detached",
    build_year: 1998,
    roof_orientation: "South-East",
    electricity_kwh_year: 3200,
    heating_type: "Gas",
    monthly_energy_bill_eur: 120,
    existing_assets: "None",
    financial_profile: "High income, prefers cash",
    notes: "Interested in sustainability and reducing carbon footprint",
  },
  {
    id: 3,
    name: "Sabine Keller",
    postal_code: "74523",
    city: "Schwäbisch Hall",
    product_interest: "Heat pump + Solar",
    household_size: 5,
    house_type: "Detached",
    build_year: 1978,
    roof_orientation: "South-West",
    electricity_kwh_year: 6000,
    heating_type: "Oil",
    monthly_energy_bill_eur: 260,
    existing_assets: "None",
    financial_profile: "Limited upfront budget, needs financing",
    notes: "Large roof area, wants to replace oil heating before regulations hit",
  },
  {
    id: 4,
    name: "Daniel Braun",
    postal_code: "74072",
    city: "Heilbronn",
    product_interest: "Solar + Battery + Wallbox",
    household_size: 2,
    house_type: "Detached",
    build_year: 2012,
    roof_orientation: "South",
    electricity_kwh_year: 3500,
    heating_type: "Heat pump",
    monthly_energy_bill_eur: 140,
    existing_assets: "None",
    financial_profile: "High income, prefers full package",
    notes: "Just bought an EV, wants full energy independence",
  },
  {
    id: 5,
    name: "Petra Lange",
    postal_code: "70563",
    city: "Stuttgart",
    product_interest: "Heat pump",
    household_size: 4,
    house_type: "Detached",
    build_year: 1970,
    roof_orientation: "South-West",
    electricity_kwh_year: 5200,
    heating_type: "Oil",
    monthly_energy_bill_eur: 250,
    existing_assets: "Solar 5 kWp",
    financial_profile: "Financing required",
    notes: "Already has solar, concerned about oil price volatility and GEG deadline",
  },
];

export default function LeadPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  // Persist lead→project mapping in localStorage
  const [projectId, setProjectId] = useState(() => {
    return localStorage.getItem(`lead_project_${id}`) || null;
  });

  const lead = useMemo(() => {
    return leads.find((item) => item.id === Number(id));
  }, [id]);

  // Create a project from lead data so the agent knows what's already collected
  const ensureProject = useCallback(async () => {
    if (projectId) return projectId;
    if (!lead) return null;

    const res = await fetch("/api/v1/projects/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: lead.name,
        customer_name: lead.name,
        postal_code: lead.postal_code || lead.postcode,
        city: lead.city || lead.area,
        product_interest: lead.product_interest?.replace(/_/g, " + "),
        household_size: lead.household_size,
        house_type: lead.house_type || null,
        build_year: lead.build_year || null,
        roof_orientation: lead.roof_orientation || null,
        electricity_kwh_year: lead.electricity_kwh_year || lead.annual_consumption_kwh,
        heating_type: lead.heating_type || null,
        monthly_energy_bill_eur: lead.monthly_energy_bill_eur || null,
        existing_assets: lead.existing_assets || null,
        financial_profile: lead.financial_profile || lead.budget_band,
        notes: lead.notes || lead.customer_goal,
      }),
    });
    const project = await res.json();
    setProjectId(project.id);
    localStorage.setItem(`lead_project_${id}`, project.id);
    return project.id;
  }, [projectId, lead, id]);

  const handleOpenChat = useCallback(async () => {
    const pid = await ensureProject();
    navigate(`/projects/${pid}/chat`);
  }, [ensureProject, navigate]);

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
  const getLeadGoal = (lead) => lead.notes || lead.customer_goal || "—";

  if (!lead) {
    return (
      <div className="lead-page">
        <div className="lead-page-container">
          <button className="back-link-btn" onClick={() => navigate("/form")}>
            <ArrowLeft size={18} />
            Back
          </button>

          <div className="lead-not-found-card">
            <h2>Lead not found</h2>
            <p>The requested customer profile does not exist.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="lead-page">
      <div className="dashboard-bg-glow dashboard-glow-1"></div>
      <div className="dashboard-bg-glow dashboard-glow-2"></div>
      <div className="dashboard-grid-overlay"></div>

      <div className="lead-page-container">
        <motion.div
          className="lead-page-header"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <button className="back-link-btn" onClick={() => navigate("/form")}>
            <ArrowLeft size={18} />
            Back
          </button>

          <div className="lead-page-title-row">
            <div>
              <p className="dashboard-kicker">Lead Detail Workspace</p>
              <h1>{lead.name}</h1>
              <p className="lead-page-subtitle">
                Review this customer profile and prepare the sales conversation.
              </p>
            </div>

            <span className="lead-preview-tag">
              {formatProduct(lead.product_interest)}
            </span>
          </div>
        </motion.div>

        <motion.div
          className="lead-detail-layout"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08 }}
        >
          <div className="lead-detail-left">
            <div className="lead-info-card">
              <div className="lead-info-header">
                <div>
                  <p className="dashboard-kicker">Customer Overview</p>
                  <h2>{lead.name}</h2>
                </div>
                <span className="lead-status-badge">Active Lead</span>
              </div>

              <div className="lead-info-grid">
                <div className="lead-info-item">
                  <span><MapPin size={16} /> City</span>
                  <p>{getLeadLocation(lead)}</p>
                </div>

                <div className="lead-info-item">
                  <span><MapPin size={16} /> Postal Code</span>
                  <p>{getLeadPostalCode(lead)}</p>
                </div>

                <div className="lead-info-item">
                  <span><Users size={16} /> Household Size</span>
                  <p>{lead.household_size || "—"} people</p>
                </div>

                <div className="lead-info-item">
                  <span><Zap size={16} /> Electricity Usage</span>
                  <p>{getLeadUsage(lead)} kWh</p>
                </div>

                <div className="lead-info-item">
                  <span><Wallet size={16} /> Budget / Profile</span>
                  <p>{getLeadBudget(lead)}</p>
                </div>

                <div className="lead-info-item">
                  <span><Target size={16} /> Product Interest</span>
                  <p>{formatProduct(lead.product_interest)}</p>
                </div>

                <div className="lead-info-item">
                  <span><Home size={16} /> House Type</span>
                  <p>{lead.house_type || "—"}</p>
                </div>

                <div className="lead-info-item">
                  <span><Calendar size={16} /> Build Year</span>
                  <p>{lead.build_year || "—"}</p>
                </div>

                <div className="lead-info-item">
                  <span><MapPin size={16} /> Roof Orientation</span>
                  <p>{lead.roof_orientation || "—"}</p>
                </div>

                <div className="lead-info-item">
                  <span><Flame size={16} /> Heating Type</span>
                  <p>{lead.heating_type || "—"}</p>
                </div>

                <div className="lead-info-item">
                  <span><Wallet size={16} /> Monthly Energy Bill</span>
                  <p>
                    {lead.monthly_energy_bill_eur
                      ? `€${lead.monthly_energy_bill_eur}`
                      : "—"}
                  </p>
                </div>

                <div className="lead-info-item">
                  <span><FileText size={16} /> Existing Assets</span>
                  <p>{lead.existing_assets || "—"}</p>
                </div>

                <div className="lead-info-item full-width">
                  <span><FileText size={16} /> Notes / Goal</span>
                  <p>{getLeadGoal(lead)}</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: "14px", marginTop: "24px" }}>
                <button
                  className="primary-btn"
                  onClick={handleOpenChat}
                  style={{ minHeight: "48px", padding: "0 28px", fontSize: "0.95rem", fontWeight: 600 }}
                >
                  <MessageCircle size={18} style={{ marginRight: 8 }} />
                  Start Sales Coaching
                </button>
              </div>
            </div>

            <div className="lead-summary-card">
              <p className="dashboard-kicker">Suggested Sales Angle</p>
              <h3>How to approach this lead</h3>
              <p>
                Focus on the customer's main priority, explain the long-term
                value of the selected product, and connect the recommendation
                to their household size, energy usage, current heating setup,
                and financial profile.
              </p>
            </div>
          </div>


        </motion.div>
      </div>
    </div>
  );
}
