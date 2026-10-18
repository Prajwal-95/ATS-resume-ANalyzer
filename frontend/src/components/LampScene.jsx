import { useEffect, useRef, useState } from 'react';

export default function LampScene({ onToggle = () => {} }) {
  const [isOn, setIsOn] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [dragX, setDragX] = useState(0);
  const [dragY, setDragY] = useState(0);
  const startX = useRef(0);
  const startY = useRef(0);
  const stringPathRef = useRef(null);
  const handleRef = useRef(null);

  const updateString = (x, y) => {
    if (stringPathRef.current) {
      stringPathRef.current.setAttribute('d', 'M 0 0 L ' + x + ' ' + (80 + y));
    }
  };

  const resetHandle = () => {
    setDragX(0);
    setDragY(0);
    updateString(0, 0);
  };

  const handlePointerDown = (e) => {
    setDragging(true);
    startX.current = e.clientX;
    startY.current = e.clientY;
    if (handleRef.current && handleRef.current.setPointerCapture) {
      try {
        handleRef.current.setPointerCapture(e.pointerId);
      } catch (_) {}
    }
  };

  const handlePointerMove = (e) => {
    if (!dragging) return;
    let dx = (e.clientX - startX.current) * 0.3;
    let dy = Math.max(0, e.clientY - startY.current) * 0.6;
    dx = Math.max(-35, Math.min(35, dx));
    dy = Math.min(180, dy);
    setDragX(dx);
    setDragY(dy);
    updateString(dx, dy);
  };

  const handlePointerUp = () => {
    if (!dragging) return;
    setDragging(false);
    const pulled = dragY > 30;
    resetHandle();
    if (pulled) {
      setIsOn((prev) => {
        const next = !prev;
        onToggle(next);
        return next;
      });
    }
  };

  const handlePointerCancel = () => {
    if (!dragging) return;
    setDragging(false);
    resetHandle();
  };

  useEffect(() => {
    const handle = handleRef.current;
    if (!handle) return;
    const move = (e) => handlePointerMove(e);
    const up = () => handlePointerUp();
    const cancel = () => handlePointerCancel();
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    window.addEventListener('pointercancel', cancel);
    return () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointercancel', cancel);
    };
  }, [dragging, dragY]);

  useEffect(() => {
    const handle = handleRef.current;
    if (!handle) return;
    const handleKey = (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        setIsOn((prev) => {
          const next = !prev;
          onToggle(next);
          return next;
        });
      }
    };
    handle.addEventListener('keydown', handleKey);
    return () => handle.removeEventListener('keydown', handleKey);
  }, []);

  useEffect(() => {
    onToggle(isOn);
  }, [isOn]);

  return (
    <section className="lamp-side">
      <div className="prompt">
        <span>Pull the string to turn on</span>
        <i aria-hidden="true"></i>
      </div>
      <div className="lamp-container" id="lampContainer">
        <div className="lamp-glow"></div>
        <div className="lamp-head"></div>
        <div className="light-beam"></div>
        <div className="lamp-stem"></div>
        <div className="lamp-base"></div>
        <div className="desk-surface"></div>

        <svg className="string-svg" aria-hidden="true">
          <path id="stringPath" ref={stringPathRef} d="M 0 0 L 0 80"></path>
        </svg>

        <div
          className="string-handle"
          id="stringHandle"
          ref={handleRef}
          aria-label="Pull lamp string"
          role="button"
          tabIndex={0}
          onPointerDown={handlePointerDown}
          style={{ transform: `translate(${dragX}px, ${dragY}px)` }}
        ></div>
      </div>
    </section>
  );
}
