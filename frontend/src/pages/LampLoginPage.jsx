import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AnimatedLampLogin from '../components/AnimatedLampLogin';
import { useAuth } from '../context/AuthContext';

export default function LampLoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async ({ email, password }) => {
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      // Redirect to the page the user originally intended to visit,
      // or fall back to /history if they navigated to /login directly.
      const from = location.state?.from?.pathname || '/history';
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Login failed. Please check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatedLampLogin
      mode="login"
      onLogin={handleLogin}
      error={error}
      loading={loading}
    />
  );
}