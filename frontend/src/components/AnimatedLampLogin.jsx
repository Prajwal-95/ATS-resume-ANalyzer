import { useLamp } from '../context/LampContext';
import LampScene from './LampScene';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import '../styles/lamp.css';

export default function AnimatedLampLogin({ mode = 'login', onLogin, onRegister, error, loading }) {
  const { lampOn, setLampOn } = useLamp();
  const isLogin = mode === 'login';

  const createFireflies = () => {
    const fireflies = [];
    for (let i = 0; i < 18; i++) {
      const size = Math.random() * 4 + 3;
      const dur = Math.random() * 30 + 35;
      const delay = Math.random() * 3;
      const positions = [];
      for (let n = 1; n <= 5; n++) {
        positions.push({
          x: Math.random() * 100,
          y: Math.random() * 100,
        });
      }
      fireflies.push({ size, dur, delay, positions });
    }
    return fireflies;
  };

  const fireflies = lampOn ? createFireflies() : [];

  return (
    <div className={`lamp-auth-room${lampOn ? ' on' : ''}`} aria-label="Animated lamp authentication">
      <div className="room-light"></div>
      <div className="fireflies">
        {fireflies.map((f, idx) => (
          <span
            key={idx}
            className="firefly"
            style={{
              width: f.size + 'px',
              height: f.size + 'px',
              '--duration': f.dur + 's',
              '--delay': f.delay + 's',
              '--x1': f.positions[0].x + 'vw',
              '--y1': f.positions[0].y + 'vh',
              '--x2': f.positions[1].x + 'vw',
              '--y2': f.positions[1].y + 'vh',
              '--x3': f.positions[2].x + 'vw',
              '--y3': f.positions[2].y + 'vh',
              '--x4': f.positions[3].x + 'vw',
              '--y4': f.positions[3].y + 'vh',
              '--x5': f.positions[4].x + 'vw',
              '--y5': f.positions[4].y + 'vh',
            }}
          ></span>
        ))}
      </div>

      <LampScene onToggle={setLampOn} initialOn={lampOn} />

      <section className="login-side">
        {isLogin ? (
          <LoginForm onSubmit={onLogin} error={error} loading={loading} />
        ) : (
          <RegisterForm onSubmit={onRegister} error={error} loading={loading} />
        )}
      </section>
    </div>
  );
}