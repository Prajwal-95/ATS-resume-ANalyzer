import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AnimatedLampLogin from '../components/AnimatedLampLogin';
import { useAuth } from '../context/AuthContext';

export default function LampRegisterPage() {
  const { register } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async ({ username, email, password }) => {
    setError('');
    setLoading(true);
    try {
      await register(email, username, password);
      navigate('/history');
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Registration failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatedLampLogin
      mode="register"
      onRegister={handleRegister}
      error={error}
      loading={loading}
    />
  );
}
