import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const features = [
  {
    title: "Keyword Analysis",
    description: "See exactly which job description keywords appear in your resume and which are missing.",
    icon: "🔍",
  },
  {
    title: "Technical Skill Matching",
    description: "Understand how your technical skills align with the requirements of the role.",
    icon: "🛠",
  },
  {
    title: "Resume Structure",
    description: "Get feedback on section layout, formatting, and ATS readability.",
    icon: "📐",
  },
  {
    title: "Actionable Suggestions",
    description: "Receive concrete, evidence-based recommendations to improve your resume.",
    icon: "💡",
  },
];

const steps = [
  { number: "1", title: "Upload", description: "Upload your resume in PDF or DOCX format." },
  { number: "2", title: "Add Job Description", description: "Paste the job posting you're applying for." },
  { number: "3", title: "Analyze", description: "Run the analysis and get your ATS compatibility score." },
  { number: "4", title: "Improve", description: "Use the suggestions to strengthen your resume." },
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-b from-primary-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
              Check Your Resume{" "}
              <span className="text-primary-600">ATS Score</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
              Upload your resume, add the job description, and discover how well your
              resume matches the role.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link to="/upload" className="btn-primary px-8 py-3 text-base">
                Upload Resume
              </Link>
              <Link to="/upload?demo=1" className="btn-secondary px-8 py-3 text-base">
                Try Demo
              </Link>
            </div>
            <p className="mt-6 text-sm text-gray-500">
              Free • No credit card required • Your data is never stored
            </p>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="card"
            >
              <div className="text-3xl">{f.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-2 text-sm text-gray-600">{f.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-3xl font-bold text-gray-900">How It Works</h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-gray-600">
            Our transparent scoring engine analyzes your resume against the job description using clear criteria.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s, i) => (
              <div key={s.number} className="relative">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-600 text-lg font-bold text-white">
                  {s.number}
                </div>
                {i < steps.length - 1 && (
                  <div className="absolute left-14 top-6 hidden h-0.5 w-full bg-gray-200 lg:block"></div>
                )}
                <h3 className="mt-4 text-lg font-semibold text-gray-900">{s.title}</h3>
                <p className="mt-2 text-sm text-gray-600">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ATS explanation */}
      <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900">What is an ATS Score?</h2>
          <p className="mt-4 text-gray-600">
            Applicant Tracking Systems (ATS) are software used by employers to filter resumes before
            a human reviews them. They scan for keywords, skills, and formatting to rank candidates.
          </p>
          <p className="mt-4 text-gray-600">
            Our score is an <strong>ATS-style compatibility estimate</strong> based on transparent,
            documented criteria. Every ATS system is different and many use proprietary algorithms,
            so your actual scores may vary. Use this as a guide, not a guarantee.
          </p>
          <div className="mt-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
            <strong>Note:</strong> The ATS scoring weights shown here are configurable and are not intended
            to represent the exact algorithm of any specific ATS platform.
          </div>
        </div>
      </section>
    </div>
  );
}
