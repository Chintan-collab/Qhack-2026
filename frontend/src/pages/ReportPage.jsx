import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download,
  Sparkles,
  MapPin,
  Sun,
  BadgeEuro,
  ShieldCheck,
  Lightbulb,
  Wallet,
  Target,
  CheckCircle2,
} from "lucide-react";

export default function ReportPage() {
  const navigate = useNavigate();

  const report = useMemo(() => {
    const raw = localStorage.getItem("reportData");
    return raw ? JSON.parse(raw) : null;
  }, []);

  if (!report) {
    return (
      <div className="report-page-wrapper">
        <div className="background-blobs">
          <div className="blob blob-1"></div>
          <div className="blob blob-2"></div>
          <div className="blob blob-3"></div>
        </div>

        <div className="empty-report-state">
          <h2>No report found</h2>
          <p>Please generate a report first to view the full AI sales analysis.</p>
          <button className="primary-btn" onClick={() => navigate("/form")}>
            Go to Form
          </button>
        </div>
      </div>
    );
  }

  const confidenceValue = Number(report.confidence || 0);

  return (
    <div className="report-page-wrapper">
      <div className="background-blobs">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
      </div>

      <section className="report-page-layout">
        <motion.div
          className="report-topbar"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
        >
          <button className="back-link-btn" onClick={() => navigate("/form")}>
            <ArrowLeft size={18} />
            Back to Form
          </button>

          <div className="report-topbar-actions">
            <button className="secondary-btn" onClick={() => window.print()}>
              <Download size={18} />
              Export / Print
            </button>
          </div>
        </motion.div>

        <motion.section
          className="report-hero-card"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65 }}
        >
          <div className="report-hero-left">
            <div className="badge">
              <Sparkles size={16} />
              <span>AI Generated Sales Intelligence</span>
            </div>

            <h1>
              Lead report for
              <span className="gradient-text"> sales-ready action</span>
            </h1>

            <p className="report-hero-text">
              A structured breakdown of customer profile, package recommendations,
              financing options, AI guidance, and report confidence.
            </p>
          </div>

          <div className="report-hero-metrics">
            <div className="hero-metric-card">
              <span>Best Package</span>
              <h3>{report.best_package || "N/A"}</h3>
            </div>

            <div className="hero-metric-card">
              <span>Confidence</span>
              <h3>{confidenceValue}/100</h3>
            </div>
          </div>
        </motion.section>

        <div className="report-main-grid">
          <motion.div
            className="report-left-column"
            initial={{ opacity: 0, x: -22 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.65, delay: 0.1 }}
          >
            <section className="report-glass-card">
              <div className="card-title-row">
                <div className="card-title-left">
                  <MapPin size={18} />
                  <h2>Customer Summary</h2>
                </div>
              </div>

              <div className="summary-grid">
                <div className="summary-item">
                  <span>Postcode</span>
                  <p>{report.customer_summary?.postcode || "—"}</p>
                </div>

                <div className="summary-item">
                  <span>Product Interest</span>
                  <p>{report.customer_summary?.product_interest || "—"}</p>
                </div>

                <div className="summary-item">
                  <span>Budget Band</span>
                  <p>{report.customer_summary?.budget_band || "—"}</p>
                </div>

                <div className="summary-item">
                  <span>Customer Goal</span>
                  <p>{report.customer_summary?.customer_goal || "—"}</p>
                </div>

                <div className="summary-item full-width">
                  <span>Estimated Profile</span>
                  <p>{report.customer_summary?.estimated_profile || "—"}</p>
                </div>
              </div>
            </section>

            <section className="report-glass-card">
              <div className="card-title-row">
                <div className="card-title-left">
                  <Sun size={18} />
                  <h2>Market Context</h2>
                </div>
              </div>

              <p className="report-text-block">
                {report.market_context?.summary || "No market context available."}
              </p>

              <div className="context-chip-row">
                <div className="context-chip">
                  <span>Relevance Signal</span>
                  <strong>{report.market_context?.relevance_signal || "Estimated"}</strong>
                </div>
              </div>
            </section>

            <section className="report-glass-card">
              <div className="card-title-row">
                <div className="card-title-left">
                  <Target size={18} />
                  <h2>Recommended Packages</h2>
                </div>
              </div>

              <div className="package-grid">
                {(report.recommended_packages || []).map((pkg) => (
                  <div
                    className={`package-card ${
                      pkg.name === report.best_package ? "package-card-featured" : ""
                    }`}
                    key={pkg.name}
                  >
                    <div className="package-header">
                      <h3>{pkg.name}</h3>
                      {pkg.name === report.best_package ? (
                        <span className="featured-tag">Best Fit</span>
                      ) : null}
                    </div>

                    <p className="package-system">{pkg.system}</p>

                    <div className="package-metrics">
                      <div>
                        <span>Capex</span>
                        <p>€{pkg.capex}</p>
                      </div>
                      <div>
                        <span>Annual Savings</span>
                        <p>€{pkg.annual_savings}</p>
                      </div>
                    </div>

                    {pkg.fit_reason ? (
                      <div className="package-extra-info">
                        <span>Fit Reason</span>
                        <p>{pkg.fit_reason}</p>
                      </div>
                    ) : null}

                    {pkg.target_customer ? (
                      <div className="package-extra-info">
                        <span>Target Customer</span>
                        <p>{pkg.target_customer}</p>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>

            <section className="report-glass-card">
              <div className="card-title-row">
                <div className="card-title-left">
                  <Wallet size={18} />
                  <h2>Financing Options</h2>
                </div>
              </div>

              <div className="finance-grid">
                {(report.financing_options || []).map((option) => (
                  <div
                    className={`finance-card ${
                      option.recommended ? "finance-card-featured" : ""
                    }`}
                    key={option.type}
                  >
                    <div className="package-header">
                      <h3>{option.type}</h3>
                      {option.recommended ? (
                        <span className="featured-tag">Recommended</span>
                      ) : null}
                    </div>

                    <div className="finance-metric">
                      <span>Monthly</span>
                      <p>€{option.monthly_payment}</p>
                    </div>

                    <div className="finance-metric">
                      <span>Total Cost</span>
                      <p>€{option.total_cost}</p>
                    </div>

                    {option.fit_reason ? (
                      <div className="package-extra-info">
                        <span>Why It Fits</span>
                        <p>{option.fit_reason}</p>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>
          </motion.div>

          <motion.div
            className="report-right-column"
            initial={{ opacity: 0, x: 22 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.65, delay: 0.15 }}
          >
            <section className="report-side-card ai-highlight-card">
              <div className="card-title-left">
                <Lightbulb size={18} />
                <h2>AI Summary</h2>
              </div>
              <p>{report.ai_summary || "No AI summary available."}</p>
            </section>

            <section className="report-side-card">
              <div className="card-title-left">
                <Target size={18} />
                <h2>Best Package Insights</h2>
              </div>

              <div className="quick-summary-list">
                <div className="quick-summary-item">
                  <span>Fit Reason</span>
                  <strong>{report.best_package_details?.fit_reason || "Not available"}</strong>
                </div>

                <div className="quick-summary-item">
                  <span>Sales Pitch</span>
                  <strong>{report.best_package_details?.sales_pitch || "Not available"}</strong>
                </div>
              </div>
            </section>

            <section className="report-side-card">
              <div className="card-title-left">
                <Wallet size={18} />
                <h2>Recommended Financing</h2>
              </div>

              <div className="quick-summary-list">
                <div className="quick-summary-item">
                  <span>Suggested Option</span>
                  <strong>{report.recommended_financing?.type || "Not available"}</strong>
                </div>

                <div className="quick-summary-item">
                  <span>Why It Fits</span>
                  <strong>{report.recommended_financing?.fit_reason || "Not available"}</strong>
                </div>
              </div>
            </section>

            <section className="report-side-card">
              <div className="card-title-left">
                <Lightbulb size={18} />
                <h2>Installer Pitch Guidance</h2>
              </div>

              <div className="quick-summary-list">
                <div className="quick-summary-item">
                  <span>Recommended Opening</span>
                  <strong>
                    {report.installer_pitch?.recommended_opening || "Not available"}
                  </strong>
                </div>

                <div className="quick-summary-item">
                  <span>Likely Objection</span>
                  <strong>
                    {report.installer_pitch?.likely_objection || "Not available"}
                  </strong>
                </div>

                <div className="quick-summary-item">
                  <span>Sales Focus</span>
                  <strong>{report.installer_pitch?.sales_focus || "Not available"}</strong>
                </div>
              </div>
            </section>

            <section className="report-side-card confidence-card">
              <div className="card-title-left">
                <ShieldCheck size={18} />
                <h2>Confidence Score</h2>
              </div>

              <div className="confidence-ring-wrapper">
                <div className="confidence-ring">
                  <span>{confidenceValue}</span>
                </div>
              </div>

              <p className="confidence-text">
                {confidenceValue >= 80
                  ? "High confidence report based on available inputs."
                  : confidenceValue >= 60
                  ? "Moderate confidence with some estimated fields."
                  : "Lower confidence due to missing information."}
              </p>
            </section>

            <section className="report-side-card assumptions-card">
              <div className="card-title-left">
                <CheckCircle2 size={18} />
                <h2>Assumptions</h2>
              </div>

              {(report.assumptions || []).length ? (
                <ul className="assumption-list">
                  {report.assumptions.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>No assumptions were needed for this request.</p>
              )}
            </section>

            <section className="report-side-card quick-summary-card">
              <div className="card-title-left">
                <BadgeEuro size={18} />
                <h2>Quick Overview</h2>
              </div>

              <div className="quick-summary-list">
                <div className="quick-summary-item">
                  <span>Best package</span>
                  <strong>{report.best_package || "N/A"}</strong>
                </div>
                <div className="quick-summary-item">
                  <span>Packages generated</span>
                  <strong>{(report.recommended_packages || []).length}</strong>
                </div>
                <div className="quick-summary-item">
                  <span>Finance options</span>
                  <strong>{(report.financing_options || []).length}</strong>
                </div>
              </div>
            </section>
          </motion.div>
        </div>
      </section>
    </div>
  );
}