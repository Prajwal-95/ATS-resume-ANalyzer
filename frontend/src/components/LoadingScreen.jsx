import { useState, useEffect } from "react";

const STEPS = [
  "Reading resume...",
  "Extracting skills...",
  "Analyzing job description...",
  "Comparing keywords...",
  "Calculating ATS score...",
];

export default function LoadingScreen() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative h-16 w-16">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
      </div>
      <div className="mt-6 space-y-2 text-center">
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={`text-sm ${i === step ? "font-medium text-primary-600" : i < step ? "text-gray-400" : "text-gray-300"}`}
          >
            {i < step ? "✓ " : ""}
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
