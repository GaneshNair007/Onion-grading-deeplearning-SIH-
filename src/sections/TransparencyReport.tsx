import { motion } from 'framer-motion'
import GlassCard from '../components/GlassCard'
import { FileCheck, QrCode, ShieldCheck, UserCheck } from 'lucide-react'

const reportFields = [
  ['REPORT ID', 'RPT-2026-SIH-001'],
  ['BATCH ID', 'ONION-PROC-BCH-892'],
  ['PROCUREMENT CENTRE', 'NASIK CENTRAL MANDI #04'],
  ['INSPECTION OFFICER', 'OFFICER ID #4029'],
  ['POLICY STAMP', 'GOVT-POLICY-v2.4 (URS ENABLED)'],
  ['TOTAL SCAN COUNT', '124 BULBS'],
  ['CALIBRATION SCALE', 'ARUCO MARKER #12 (1.42 px/mm)'],
]

export default function TransparencyReport() {
  return (
    <section className="py-24 px-6 bg-app-bg relative">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Header */}
        <div className="space-y-4 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            className="flex items-center gap-3"
          >
            <span className="w-8 h-0.5 bg-cyan-dark" />
            <span className="font-mono text-xs font-bold tracking-widest text-cyan-dark uppercase">
              AUDITABLE AUDIT EVIDENCE TRAIL
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="section-heading"
          >
            EVERY DECISION <span className="text-cyan-dark">EVERY DECISION LEAVES A TRACE.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="text-lg md:text-xl text-text-sec leading-relaxed font-medium"
          >
            The instant digital quality report is the primary procurement deliverable — replacing subjective disputes with auditable, image-backed evidence and QR validation.
          </motion.p>
        </div>

        {/* Mock Report + Feature Highlights */}
        <div className="grid lg:grid-cols-12 gap-8 items-start">
          
          {/* Digital Report Card */}
          <GlassCard className="lg:col-span-7 p-0 overflow-hidden border-white">
            <div className="p-6 md:p-8 bg-graphite text-white flex items-center justify-between border-b border-white/10">
              <div>
                <span className="font-mono text-[9px] font-bold text-cyan-glow tracking-widest uppercase">INSTANT DELIVERABLE</span>
                <h3 className="font-mono text-base font-extrabold text-white tracking-wider uppercase mt-1">
                  DIGITAL QUALITY AUDIT REPORT
                </h3>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-cyan-glow border border-white/10">
                <QrCode className="w-6 h-6" />
              </div>
            </div>

            <div className="p-6 md:p-8 space-y-4 font-mono text-xs">
              {reportFields.map(([k, v]) => (
                <div key={k} className="flex flex-wrap items-center justify-between py-2 border-b border-black/5 gap-2">
                  <span className="text-text-muted font-bold">{k}</span>
                  <span className="font-extrabold text-graphite">{v}</span>
                </div>
              ))}
            </div>

            <div className="p-6 bg-surface-subtle border-t border-black/5 flex items-center justify-between font-mono text-xs">
              <span className="text-emerald-700 font-extrabold flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" /> REPORT VERIFIED & SIGNED
              </span>
              <span className="text-text-muted font-medium"> CORE MVP</span>
            </div>
          </GlassCard>

          {/* Value Props Column */}
          <div className="lg:col-span-5 space-y-4">
            {[
              {
                title: 'Structured Evidence Trail',
                body: 'Every detected onion is logged with its calibrated diameter in mm, visible defect labels, acoustic condition score, and AI confidence level.',
                icon: FileCheck,
              },
              {
                title: 'Policy Versioning Stamp',
                body: 'Active Grade A / URS thresholds are permanently bound into the report metadata, ensuring grades are defensible against stated policy rules.',
                icon: ShieldCheck,
              },
              {
                title: 'Human-in-the-Loop Authority',
                body: 'The officer retains final decision authority. Any manual override is recorded in the audit log with a required reason code.',
                icon: UserCheck,
              },
            ].map((item, i) => {
              const Icon = item.icon
              return (
                <GlassCard key={item.title} delay={i * 0.1} className="p-6 border-white space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-soft-cyan text-cyan-dark flex items-center justify-center">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h4 className="font-mono text-xs font-extrabold text-graphite uppercase tracking-wider">{item.title}</h4>
                  </div>
                  <p className="text-xs text-text-sec leading-relaxed font-medium pl-12">{item.body}</p>
                </GlassCard>
              )
            })}
          </div>

        </div>

      </div>
    </section>
  )
}

