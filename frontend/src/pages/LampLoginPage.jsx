import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AnimatedLampLogin from '../components/AnimatedLampLogin';
import { useAuth } from '../context/AuthContext';

export default function LampLoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async ({ email, password }) => {
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/history');
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
