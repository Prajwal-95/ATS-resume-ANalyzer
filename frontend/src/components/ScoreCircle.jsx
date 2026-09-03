import { motion } from "framer-motion";

export default function ScoreCircle({ score, size = 180, strokeWidth = 12 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));

  const getColor = (value) => {
    if (value >= 80) return "#10b981"; // Green
    if (value >= 60) return "#3b82f6"; // Blue
    if (value >= 40) return "#f59e0b"; // Amber
    return "#ef4444"; // Red
  };

  const color = getColor(progress);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - (progress / 100) * circumference }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-4xl font-bold" style={{ color }}>
          {Math.round(progress)}
        </div>
        <div className="text-sm font-medium text-gray-500">/ 100</div>
      </div>
    </div>
  );
}
