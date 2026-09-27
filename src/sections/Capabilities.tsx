import { Eye, Waves, FileText } from 'lucide-react'

const items = [
  {
    num: '01',
    icon: Eye,
    color: 'text-blue-acc',
    bg: 'bg-soft-blue',
    label: 'VISION PIPELINE',
    title: 'Detect surface defects',
    body: 'Camera capture identifies visible damage, sprouting, bruising, size and shape. Each onion is measured against configurable grade parameters — not a fixed universal rule.',
  },
  {
    num: '02',
    icon: Waves,
    color: 'text-cyan-acc',
    bg: 'bg-soft-cyan',
    label: 'ACOUSTIC SCREENING',
    title: 'Screen internal-quality risk',
    body: 'A controlled acoustic signal is emitted and the response is captured. Items with readings that diverge from a healthy baseline are flagged for manual review — the system raises a question, not a verdict.',
  },
  {
    num: '03',
    icon: FileText,
    color: 'text-lav-acc',
    bg: 'bg-soft-lav',
    label: 'GRADE ENGINE',
    title: 'Generate a grading report',
    body: 'Every batch produces an evidence-backed output: Grade A, Grade URS, Manual Review and Rejected classifications with a timestamped, downloadable audit record.',
  },
]

export default function Capabilities() {
  return (
    <section id="capabilities" className="section-pad bg-app-bg">
      <div className="max-w-7xl mx-auto px-6">

        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="tech-label text-cyan-acc mb-4">Capabilities</p>
          <h2 className="text-graphite font-bold leading-tight mb-5" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
            A more consistent inspection workflow.
          </h2>
          <p className="text-text-sec text-lg leading-relaxed">
            Computer vision measures the visible. Acoustic screening investigates what the camera cannot.
          </p>
        </div>

        {/* Glass cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {items.map(({ num, icon: Icon, color, bg, label, title, body }) => (
            <div key={num} className="glass p-8 flex flex-col gap-5 hover:shadow-glass-hover transition-shadow duration-300 group">
              {/* Icon */}
              <div className={`w-12 h-12 ${bg} rounded-2xl flex items-center justify-center`}>
                <Icon size={22} className={color} />
              </div>

              {/* Label */}
              <div className="flex items-center justify-between">
                <span className="tech-label">{label}</span>
                <span className="tech-label text-[9px] text-text-sec/50">{num}</span>
              </div>

              {/* Title */}
              <h3 className="text-graphite text-xl font-semibold leading-snug">{title}</h3>

              {/* Body */}
              <p className="text-text-sec text-sm leading-relaxed flex-1">{body}</p>

              {/* Accent bar */}
              <div className={`w-8 h-0.5 ${color.replace('text-', 'bg-')} group-hover:w-16 transition-all duration-300`} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
