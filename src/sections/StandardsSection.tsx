import { motion } from 'framer-motion'
import { CheckCircle2, Sliders } from 'lucide-react'

const tableData = [
  { param: 'Diameter', gradeA: '45–65 mm', urs: '35–70 mm' },
  { param: 'Visible Rot', gradeA: '0% (Not allowed)', urs: '0% (Not allowed)' },
  { param: 'Internal Rot (FFT)', gradeA: '0% (Resonant Peak > 180Hz)', urs: '0% (Resonant Peak > 180Hz)' },
  { param: 'Hollow Heart Void', gradeA: '0% (Not allowed)', urs: 'Max 10% Volume (URS Accepted)' },
  { param: 'Sprouting', gradeA: 'Max 2%', urs: 'Max 5% per URS policy' },
]

export default function StandardsSection() {
  return (
    <section className="py-24 px-4 md:px-8 bg-ind-dark relative">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Header */}
        <div className="space-y-4 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="flex items-center gap-3 font-mono text-xs"
          >
            <span className="w-8 h-0.5 bg-sonar-cyan" />
            <span className="font-bold tracking-widest text-sonar-cyan uppercase">
              PROCUREMENT POLICY MATRIX ()
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-heading"
          >
            STANDARDS & <br />
            <span className="text-sonar-cyan">POLICY ENGINE.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-base md:text-lg text-text-sec leading-relaxed font-mono"
          >
            Configurable AGMARK & URS · Under Relaxed Specification policy parameters. Rules are versioned and cryptographically signed with every report.
          </motion.p>
        </div>

        {/* Policy Table & Terminology Explanation */}
        <div className="grid lg:grid-cols-12 gap-8 items-start">
          
          {/* Table Card */}
          <div className="lg:col-span-8 hud-panel p-0 overflow-hidden border-white/10">
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
              <div>
                <span className="tech-micro-badge">GRADE A / URS POLICY ENGINE</span>
                <h3 className="font-mono text-xs font-bold text-white tracking-wider uppercase mt-2">
                  STARTING POLICY PARAMETERS
                </h3>
              </div>
              <Sliders className="w-5 h-5 text-sonar-cyan" />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-ind-dark border-b border-white/10 text-text-muted">
                  <tr>
                    <th className="px-6 py-4">PARAMETER</th>
                    <th className="px-6 py-4">GRADE A THRESHOLD</th>
                    <th className="px-6 py-4">GRADE URS THRESHOLD</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10 text-white">
                  {tableData.map((row) => (
                    <tr key={row.param} className="hover:bg-ind-panel transition-colors">
                      <td className="px-6 py-4 font-bold">{row.param}</td>
                      <td className="px-6 py-4 font-semibold text-emerald-400">{row.gradeA}</td>
                      <td className="px-6 py-4 font-semibold text-sonar-cyan">{row.urs}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 bg-ind-dark/80 border-t border-white/10 text-[11px] font-mono text-text-sec leading-relaxed">
              * Policy thresholds are configurable per procurement centre and recorded in report metadata.
            </div>
          </div>

          {/* URS Definition Callout Card */}
          <div className="lg:col-span-4 space-y-6 font-mono text-xs">
            <div className="hud-panel p-6 border-sonar-cyan/40 bg-ind-card space-y-4">
              <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                <div className="w-9 h-9 rounded-xl bg-sonar-cyan/10 text-sonar-cyan flex items-center justify-center border border-sonar-cyan/40">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <span className="tech-micro-badge">DEFINITION</span>
                  <h4 className="font-bold text-white tracking-wider uppercase mt-0.5">UNDER RELAXED SPECIFICATION · URS</h4>
                </div>
              </div>

              <p className="text-text-sec leading-relaxed">
                <strong className="text-white">URS (Under Relaxed Specification)</strong> is an officially defined, accepted quality procurement category — NOT a reject or defect label.
              </p>

              <div className="p-4 rounded-xl bg-ind-dark border border-white/10 text-[11px] text-sonar-cyan space-y-1">
                <p>• Grade A = Target premium/export grade</p>
                <p>• Grade URS = Accepted under the active relaxed specification</p>
                <p>• Rejected = Does not meet the active Grade A / URS policy</p>
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  )
}

