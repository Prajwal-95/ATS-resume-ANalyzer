import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function RegisterForm({ onSubmit, error, loading }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setLocalError('');
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters.');
      return;
    }
    onSubmit({ username, email, password });
  };

  const displayError = localError || error;

  return (
    <form className="glass login-card" onSubmit={handleSubmit} noValidate>
      <div className="glass-line"></div>

      <div className="login-heading">
        <h2>Create Account</h2>
        <p>Sign up to save and review your resume analyses</p>
      </div>

      <div className="inputs">
        <label className="input-wrap">
          <span className="input-icon user-icon" aria-hidden="true"></span>
          <input
            type="text"
            placeholder="Username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
          />
        </label>

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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>

        <label className="input-wrap">
          <span className="input-icon lock-icon" aria-hidden="true"></span>
          <input
            type="password"
            placeholder="Confirm Password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </label>
      </div>

      {displayError && <div className="error-message" role="alert">{displayError}</div>}

<button className="sign-in" type="submit" disabled={loading}>
        {loading ? 'Creating account...' : 'Sign Up'}
      </button>

      <div className="divider">
        <span></span>
        <b>OR CONTINUE WITH</b>
        <span></span>
      </div>

      <div className="socials">
        <div className="social-option">
          <button className="social-btn" type="button" disabled>
            <span className="google-icon">G</span> Google
          </button>
          <span className="coming-soon" aria-hidden="true">Coming Soon</span>
        </div>
        <div className="social-option">
          <button className="social-btn" type="button" disabled>
            <span className="github-icon">•</span> GitHub
          </button>
          <span className="coming-soon" aria-hidden="true">Coming Soon</span>
        </div>
      </div>

      <div className="link-text">
        Already have an account? <Link to="/login">Log in</Link>
      </div>
      <div className="brand-title">ATS Resume Score Checker</div>
    </form>
  );
}
