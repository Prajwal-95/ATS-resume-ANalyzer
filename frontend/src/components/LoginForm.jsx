import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function LoginForm({ onSubmit, error, loading }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ email, password });
  };

  return (
    <form className="glass login-card" onSubmit={handleSubmit} noValidate>
      <div className="glass-line"></div>

      <div className="login-heading">
        <h2>Welcome Back</h2>
        <p>Enter your details to access your account</p>
      </div>

      <div className="inputs">
        <label className="input-wrap">
          <span className="input-icon mail-icon" aria-hidden="true"></span>
          <input
            type="email"
            placeholder="Email Address"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>

        <label className="input-wrap">
          <span className="input-icon lock-icon" aria-hidden="true"></span>
          <input
            type="password"
            placeholder="Password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
      </div>

      {error && <div className="error-message" role="alert">{error}</div>}

      <button className="sign-in" type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>

      <div className="divider">
        <span></span>
        <b>OR CONTINUE WITH</b>
        <span></span>
      </div>

      <div className="socials">
        <button className="social-btn" type="button" disabled={loading}>
          <span className="google-icon">G</span> Google
        </button>
        <button className="social-btn" type="button" disabled={loading}>
          <span className="github-icon">•</span> GitHub
        </button>
      </div>

      <div className="link-text">
        Don't have an account? <Link to="/register">Sign up</Link>
      </div>
      <div className="brand-title">ATS Resume Score Checker</div>
    </form>
  );
}
