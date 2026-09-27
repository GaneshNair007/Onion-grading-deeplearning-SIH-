import { useState } from 'react'
import { motion } from 'framer-motion'
import { Camera, Play, RefreshCw, RotateCcw, CheckCircle2, Activity, Database, Settings, Beaker } from 'lucide-react'

type TestState = 'idle' | 'recording' | 'processing' | 'complete'

const stateLabels: Record<TestState, string> = {
  idle: 'System Ready — Awaiting Input',
  recording: 'Acquiring Acoustic Signature…',
  processing: 'Analyzing Spectral Data…',
  complete: 'Evaluation Complete',
}

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
}

export default function Prototype() {
  const [testState, setTestState] = useState<TestState>('idle')
  const [grade, setGrade] = useState<string | null>(null)

  const runDemoTest = async () => {
    if (testState !== 'idle' && testState !== 'complete') return
    setGrade(null)
    setTestState('recording')
    await delay(2200)
    setTestState('processing')
    await delay(1800)
    setGrade('Grade A — Premium')
    setTestState('complete')
  }

  const reset = () => {
    setTestState('idle')
    setGrade(null)
  }

  return (
    <main className="pt-28 pb-20 px-4 md:px-8 min-h-screen bg-bg-base relative overflow-hidden selection:bg-onion/15">
      {/* Background Decor */}
      <div className="absolute top-40 left-20 w-[500px] h-[500px] bg-onion-soft/30 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-20 right-20 w-[400px] h-[400px] bg-pastel-lavender/25 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-12 relative z-10">

        {/* ═══════ Page Header ═══════ */}
        <motion.div
          initial="hidden" animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.1 } } }}
          className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-glass-border"
        >
          <div>
            <motion.div variants={fadeUp} className="tag tag-pink w-fit mb-4">
              <Beaker size={12} />
              Experimental Lab
            </motion.div>
            <motion.h1 variants={fadeUp} className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-3">
              Acoustic Test <span className="">Inspection Bench</span>
            </motion.h1>
            <motion.p variants={fadeUp} className="text-base text-text-secondary font-sans max-w-xl leading-relaxed">
              This interactive prototype simulates the end-to-end testing pipeline. 
              In the production build, this interface will be connected to the Python backend 
              via WebSocket to control physical hardware in real-time.
            </motion.p>
          </div>

          <motion.div variants={fadeUp} className="flex items-center gap-4 px-5 py-4 rounded-2xl bg-white/60 backdrop-blur-xl border border-glass-border shadow-soft">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-success opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-accent-success" />
            </span>
            <div>
              <span className="font-sans font-semibold text-sm text-text-primary block">System Operational</span>
              <span className="text-xs text-text-muted font-sans"> · Demo Mode</span>
            </div>
          </motion.div>
        </motion.div>

        {/* ═══════ Main Layout Grid ═══════ */}
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* Main Camera / Feed View */}
          <div className="lg:col-span-8 space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className="glass-card !p-0 overflow-hidden min-h-[400px] relative group"
            >
              {/* Live Feed Image */}
              <img
                src="/image-7.png"
                alt="Live Camera Feed — Top View"
                className="w-full h-full min-h-[400px] object-cover transition-transform duration-700 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />

              {/* Camera Overlay */}
              <div className="absolute top-4 left-4 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 flex items-center gap-2">
                <Camera size={14} className="text-white" />
                <span className="text-xs font-sans font-medium text-white tracking-wide">CAM_01 · TOP VIEW</span>
              </div>

              {/* Processing Overlay */}
              {testState === 'processing' && (
                <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center transition-all">
                  <div className="flex flex-col items-center">
                    <RefreshCw className="w-10 h-10 text-white animate-spin mb-4" />
                    <span className="text-white font-sans font-medium tracking-wide">Processing visual assessment…</span>
                  </div>
                </div>
              )}

              {/* Grade Result Badge */}
              {grade && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-xl px-8 py-4 rounded-2xl shadow-blush border border-onion/10 flex items-center gap-4"
                >
                  <CheckCircle2 className="w-8 h-8 text-accent-success" />
                  <div>
                    <p className="text-xs text-text-muted font-sans font-semibold uppercase tracking-wider">Assessment outcome</p>
                    <p className="text-xl font-display font-bold text-text-primary">{grade}</p>
                  </div>
                </motion.div>
              )}
            </motion.div>

            {/* Test Controls Bar */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="glass-card !p-6"
            >
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-display text-lg font-semibold text-text-primary mb-1">Inspection Sequence</h3>
                  <p className={`text-sm font-sans font-medium ${
                    testState === 'complete' ? 'text-accent-success' :
                    testState === 'recording' ? 'text-onion' :
                    testState === 'processing' ? 'text-accent-warn' :
                    'text-text-secondary'
                  }`}>
                    {stateLabels[testState]}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={runDemoTest}
                    disabled={testState === 'recording' || testState === 'processing'}
                    className="btn-onion !py-3 !px-6 !text-sm"
                  >
                    {testState === 'recording' || testState === 'processing' ? (
                      <><RefreshCw size={16} className="animate-spin" /> In Progress</>
                    ) : (
                      <><Play size={16} className="fill-current" /> Run Assessment</>
                    )}
                  </button>

                  {testState === 'complete' && (
                    <button
                      onClick={reset}
                      className="p-3 rounded-xl bg-white/60 hover:bg-white border border-glass-border text-text-secondary hover:text-text-primary transition-all shadow-soft"
                    >
                      <RotateCcw size={16} />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          </div>

          {/* ═══════ Right Sidebar ═══════ */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* System Integration Info */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="glass-card"
            >
              <div className="flex items-center gap-3 border-b border-glass-border pb-4 mb-5">
                <div className="w-9 h-9 rounded-xl bg-onion-soft/60 flex items-center justify-center text-onion">
                  <Database size={18} />
                </div>
                <h3 className="font-display text-lg font-semibold text-text-primary">Backend Integration</h3>
              </div>
              <p className="text-sm text-text-secondary font-sans leading-[1.75] mb-4">
                This interface is structured for live backend integration. Once connected, it will:
              </p>
              <ul className="space-y-3 text-sm text-text-secondary font-sans">
                {[
                  'Trigger the solenoid physical impact',
                  'Stream real-time mic data for live FFT graphing',
                  'Run ML inference and return quality grades',
                  'Generate tamper-proof digital audit reports',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-onion mt-2 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Live Sensor Telemetry */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="glass-card"
            >
              <div className="flex items-center gap-3 border-b border-glass-border pb-4 mb-5">
                <div className="w-9 h-9 rounded-xl bg-pastel-sage/60 flex items-center justify-center text-accent-success">
                  <Activity size={18} />
                </div>
                <h3 className="font-display text-lg font-semibold text-text-primary">Sensor Readout</h3>
              </div>

              <div className="space-y-5">
                {[
                  { label: 'Acoustic Resonance', value: '1.2 kHz', pct: testState === 'complete' ? 65 : testState === 'processing' ? 45 : 10, color: 'from-onion-light to-onion' },
                  { label: 'Structural Integrity', value: '98.5%', pct: testState === 'complete' ? 98 : testState === 'processing' ? 70 : 15, color: 'from-pastel-sage to-accent-success' },
                  { label: 'Moisture Content', value: '82.1%', pct: testState === 'complete' ? 82 : testState === 'processing' ? 50 : 8, color: 'from-pastel-sky to-accent-info' },
                ].map((metric) => (
                  <div key={metric.label}>
                    <div className="flex justify-between items-end mb-2">
                      <span className="text-xs font-sans font-semibold text-text-secondary uppercase tracking-wider">{metric.label}</span>
                      <span className="font-mono text-sm text-text-primary font-semibold">{metric.value}</span>
                    </div>
                    <div className="w-full bg-bg-soft rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full bg-gradient-to-r ${metric.color} transition-all duration-1000 ease-out`}
                        style={{ width: `${metric.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Hardware Configuration */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="glass-card"
            >
              <div className="flex items-center gap-3 border-b border-glass-border pb-4 mb-5">
                <div className="w-9 h-9 rounded-xl bg-pastel-lavender/60 flex items-center justify-center text-[#6B5BAD]">
                  <Settings size={18} />
                </div>
                <h3 className="font-display text-lg font-semibold text-text-primary">Hardware Config</h3>
              </div>

              <div className="space-y-3">
                {[
                  { label: 'Excitation', value: 'Solenoid 5V, 5ms pulse' },
                  { label: 'Sampling Rate', value: '44.1 kHz PCM' },
                  { label: 'FFT Window', value: '1024-point Hanning' },
                  { label: 'Frequency Range', value: '100 Hz – 8 kHz chirp' },
                  { label: 'ML Model', value: '1D-CNN (TensorFlow Lite)' },
                ].map((item) => (
                  <div key={item.label} className="flex justify-between items-center py-2 border-b border-glass-border/50 last:border-b-0">
                    <span className="text-xs font-sans font-semibold text-text-muted uppercase tracking-wider">{item.label}</span>
                    <span className="text-sm font-mono text-text-primary font-medium">{item.value}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </main>
  )
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
