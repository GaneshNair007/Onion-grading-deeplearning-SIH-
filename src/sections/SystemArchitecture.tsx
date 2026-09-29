import { motion } from 'framer-motion'
import { Camera, Mic, Cpu } from 'lucide-react'

export default function SystemArchitecture() {
  return (
    <section id="system" className="py-24 px-4 md:px-8 bg-ind-dark relative">
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
              HARDWARE + SENSOR FUSION PIPELINE
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-heading"
          >
            EDGE HARDWARE & <br />
            <span className="text-sonar-cyan">FUSION ENGINE.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-base md:text-lg text-text-sec leading-relaxed font-mono"
          >
            Dual-modal sensor fusion combining calibrated RGB camera optics and solenoid piezo acoustic transducers into an offline Raspberry Pi 4 edge controller.
          </motion.p>
        </div>

        {/* 3 Architecture Columns */}
        <div className="grid lg:grid-cols-3 gap-8 items-stretch font-mono text-xs">
          
          {/* Vision Column */}
          <div className="hud-panel p-6 space-y-6 border-white/10 flex flex-col justify-between">
            <div className="flex items-center gap-3 border-b border-white/10 pb-4">
              <div className="w-10 h-10 rounded-xl bg-ind-panel text-emerald-400 flex items-center justify-center border border-white/10">
                <Camera className="w-5 h-5" />
              </div>
              <div>
                <span className="tech-micro-badge">REQUIRED MVP</span>
                <h3 className="font-bold text-white tracking-wider uppercase mt-1">RGB OPTICAL SYSTEM</h3>
              </div>
            </div>

            <div className="space-y-3">
              {[
                { title: 'CAM RING LIGHT', desc: '1080p camera with 5500K LED ring light illumination' },
                { title: 'OPENCV SIZING', desc: 'ArUco reference marker for millimeter diameter precision' },
                { title: 'SURFACE ROT DETECT', desc: 'YOLOv8 nano model for outer rot & sprouting' },
                { title: 'COLOR GRADING', desc: 'HSV color histogram for skin tunic classification' },
              ].map((step) => (
                <div key={step.title} className="p-3.5 rounded-xl bg-ind-dark border border-white/10 space-y-1">
                  <p className="font-bold text-white">{step.title}</p>
                  <p className="text-[11px] text-text-sec">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Acoustic Differentiator Column */}
          <div className="hud-panel p-6 space-y-6 border-sonar-cyan/40 bg-ind-card flex flex-col justify-between">
            <div className="flex items-center gap-3 border-b border-white/10 pb-4">
              <div className="w-10 h-10 rounded-xl bg-sonar-cyan/10 text-sonar-cyan flex items-center justify-center border border-sonar-cyan/40">
                <Mic className="w-5 h-5" />
              </div>
              <div>
                <span className="tech-micro-badge">KEY DIFFERENTIATOR</span>
                <h3 className="font-bold text-white tracking-wider uppercase mt-1">ACOUSTIC IMPULSE BENCH</h3>
              </div>
            </div>

            <div className="space-y-3">
              {[
                { title: 'SOLENOID ACTUATOR', desc: '5V solenoid impact pin delivers 1.2 N calibrated tap' },
                { title: 'PIEZO CONTACT MIC', desc: 'High-sensitivity contact transducer captures response' },
                { title: 'PREAMP ADC', desc: '24-bit 44.1kHz audio preamplifier digitizes signal' },
                { title: 'FFT DEFECT MODEL', desc: 'Random forest regressor flags internal neck rot' },
              ].map((step) => (
                <div key={step.title} className="p-3.5 rounded-xl bg-ind-dark border border-sonar-cyan/30 space-y-1">
                  <p className="font-bold text-sonar-cyan">{step.title}</p>
                  <p className="text-[11px] text-text-sec">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Fusion & Decision Column */}
          <div className="hud-panel p-6 space-y-6 border-amber-500/40 flex flex-col justify-between">
            <div className="flex items-center gap-3 border-b border-white/10 pb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/40">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <span className="amber-micro-badge">EDGE CONTROLLER</span>
                <h3 className="font-bold text-white tracking-wider uppercase mt-1">EDGE CONTROL / URS POLICY</h3>
              </div>
            </div>

            <div className="space-y-3">
              {[
                { title: 'URS POLICY MATRIX', desc: 'Executes AGMARK & Under Relaxed Specification rules' },
                { title: 'MANUAL REVIEW FALLBACK', desc: 'Safety trigger routes low confidence to human reviewer' },
                { title: 'BATCH DENSITY REPORT', desc: 'Calculates Grade A %, URS %, and Reject %' },
                { title: 'DIGITAL VERIFICATION', desc: 'Signs report with SHA-256 hash & QR code' },
              ].map((step) => (
                <div key={step.title} className="p-3.5 rounded-xl bg-ind-dark border border-white/10 space-y-1">
                  <p className="font-bold text-amber-400">{step.title}</p>
                  <p className="text-[11px] text-text-sec">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </section>
  )
}

