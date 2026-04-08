import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  LineChart,
  Mail,
  Lock,
} from "lucide-react";

export default function HomePage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogin = (event) => {
    event.preventDefault();
    navigate("/form");
  };

  return (
    <div className="login-home-page">
      <div className="login-bg-glow login-glow-1"></div>
      <div className="login-bg-glow login-glow-2"></div>
      <div className="login-grid-overlay"></div>

      <section className="login-hero-section">
        <motion.div
          className="login-hero-left"
          initial={{ opacity: 0, x: -35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="login-brand">Cloover AI</div>

          <div className="badge">
            <Sparkles size={16} />
            <span>AI-Powered Sales Intelligence</span>
          </div>

          <h1>
            Installer financing and
            <span className="gradient-text"> sales coaching</span>
            <br />
            in one workspace
          </h1>

          <p className="login-hero-description">
            Turn lead information into financing-ready recommendations,
            structured project insights, and guided sales conversations with a
            modern AI sales workflow.
          </p>

          <div className="login-feature-list">
            <div className="login-feature-item">
              <ShieldCheck size={18} />
              <span>Smarter lead qualification</span>
            </div>

            <div className="login-feature-item">
              <LineChart size={18} />
              <span>Structured recommendations and financing insights</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="login-hero-right"
          initial={{ opacity: 0, y: 35 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.85, delay: 0.15 }}
        >
          <div className="login-card">
            <div className="login-card-header">
              <p className="section-kicker">Welcome back</p>
              <h2>Sign in to AI Sales Coach</h2>
              <p className="login-card-subtitle">
                Access your lead analysis workspace and generate sales-ready
                reports.
              </p>
            </div>

            <form className="login-form" onSubmit={handleLogin}>
              <div className="input-group">
                <label>Email address</label>
                <div className="input-shell">
                  <Mail size={18} />
                  <input
                    type="email"
                    name="email"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="input-group">
                <label>Password</label>
                <div className="input-shell">
                  <Lock size={18} />
                  <input
                    type="password"
                    name="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="login-meta-row">
                <label className="remember-row">
                  <input type="checkbox" />
                  <span>Remember me</span>
                </label>

                <button
                  type="button"
                  className="text-link-btn"
                  onClick={() => alert("Support feature coming soon")}
                >
                  Need help?
                </button>
              </div>

              <motion.button
                className="primary-btn login-submit-btn"
                type="submit"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Login
                <ArrowRight size={18} />
              </motion.button>
            </form>

            <div className="login-footer-note">
              Secure access for installer and sales workflows
            </div>
          </div>
        </motion.div>
      </section>
    </div>
  );
}