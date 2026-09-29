import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, Power, ArrowRight, Camera, Mic, Disc, ArrowDown } from 'lucide-react'
import OnionLayerInspector from '../components/OnionLayerInspector'

function TechnicalSchematic() {
  const [scanPhase, setScanPhase] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setScanPhase((prev) => (prev + 1) % 4)
    }, 1500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="relative w-full h-[500px] bg-ind-panel border border-ind-border rounded-lg overflow-hidden font-mono text-xs text-text-muted p-4 flex flex-col justify-between">
      {/* Schematic Header */}
      <div className="flex justify-between items-center border-b border-ind-border pb-2">
        <span className="flex items-center gap-2 text-off-white font-bold">
          <Activity size={14} className="text-raf-blue animate-pulse-slow" />
          SYS-INSPECT // BENCH-04
        </span>
        <span className="bg-raf-blue/10 text-raf-blue px-2 py-1 rounded">SN-9428-A</span>
      </div>

      {/* Main Diagram Area */}
      <div className="flex-1 relative mt-4 grid grid-cols-2 gap-4">
        {/* Left: Hardware setup */}
        <div className="relative border border-ind-border border-dashed p-4 flex flex-col items-center justify-center">
          <div className="absolute top-2 left-2 text-[10px]">01 · ACQUISITION</div>
          
          {/* Solenoid */}
          <div className="flex flex-col items-center mb-2">
            <div className={`w-8 h-8 rounded-sm flex items-center justify-center border transition-colors ${scanPhase === 0 ? 'bg-raf-blue/20 border-raf-blue text-raf-blue' : 'border-ind-border'}`}>
              <Power size={14} />
            </div>
            <div className="text-[10px] mt-1">CONTROLLED IMPULSE</div>
          </div>

          <ArrowDown size={14} className="my-1 opacity-50" />

          {/* Onion Cradle */}
          <div className="relative w-20 h-20 rounded-full border-2 border-ind-border-bright flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border border-ind-border border-dashed flex items-center justify-center text-ind-border-bright">
              <Disc size={20} />
            </div>
            {/* Scan Line Animation */}
            {scanPhase === 1 && (
              <div className="absolute top-0 left-0 w-full h-1 bg-raf-blue shadow-hud-glow animate-scan-line" />
            )}
          </div>

          <div className="flex w-full justify-between mt-2">
            {/* Contact Piezo */}
            <div className="flex flex-col items-center">
              <ArrowDown size={14} className="mb-1 opacity-50" />
              <div className={`w-6 h-6 rounded-sm flex items-center justify-center border transition-colors ${scanPhase === 2 ? 'bg-raf-blue/20 border-raf-blue text-raf-blue' : 'border-ind-border'}`}>
                <Mic size={12} />
              </div>
              <div className="text-[9px] mt-1">PIEZO · 0–2.5 kHz</div>
            </div>
            
            {/* Camera */}
            <div className="flex flex-col items-center">
               <ArrowDown size={14} className="mb-1 opacity-50" />
              <div className={`w-6 h-6 rounded-sm flex items-center justify-center border transition-colors ${scanPhase === 1 ? 'bg-raf-blue/20 border-raf-blue text-raf-blue' : 'border-ind-border'}`}>
                <Camera size={12} />
              </div>
              <div className="text-[9px] mt-1">RGB VISION</div>
            </div>
          </div>
        </div>

        {/* Right: Data & Decision */}
        <div className="flex flex-col gap-2">
           <div className="border border-ind-border p-2">
             <div className="text-[10px] mb-2 border-b border-ind-border pb-1">RESPONSE LOG</div>
             <div className="h-16 relative overflow-hidden flex items-center">
                {/* Fake waveform line */}
                <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 20">
                  <path d="M0,10 Q10,10 20,5 T40,15 T60,2 T80,18 T100,10" fill="none" stroke={scanPhase === 2 ? '#3B82F6' : '#374151'} strokeWidth="1" className={scanPhase === 2 ? 'animate-pulse-slow' : ''} />
                  {scanPhase === 2 && <path d="M0,10 Q10,10 20,5 T40,15 T60,2 T80,18 T100,10" fill="none" stroke="#3B82F6" strokeWidth="2" strokeDasharray="100" strokeDashoffset="0">
                     <animate attributeName="stroke-dashoffset" values="100;0" dur="1s" fill="freeze" />
                  </path>}
                </svg>
             </div>
           </div>

           <div className="flex-1 border border-ind-border p-2 flex flex-col">
              <div className="text-[10px] mb-2 border-b border-ind-border pb-1">DECISION MATRIX</div>
              <div className="flex flex-col gap-2 mt-2">
                <div className={`flex justify-between items-center px-2 py-1 border transition-colors ${scanPhase === 3 ? 'bg-grade-a/10 border-grade-a text-grade-a' : 'border-ind-border'}`}>
                  <span>GRADE A</span>
                  <span className="text-[9px]">[ ACCEPT ]</span>
                </div>
                <div className={`flex justify-between items-center px-2 py-1 border transition-colors border-ind-border`}>
                  <span>GRADE URS</span>
                  <span className="text-[9px] text-grade-urs">[ REVIEW ]</span>
                </div>
                <div className={`flex justify-between items-center px-2 py-1 border transition-colors border-ind-border`}>
                  <span>REJECTED</span>
                  <span className="text-[9px] text-grade-rejected">[ REJECT ]</span>
                </div>
              </div>
           </div>
        </div>
      </div>

      {/* Sensor Health Chips */}
      <div className="mt-4 pt-2 border-t border-ind-border flex justify-between">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
             <span className="w-2 h-2 rounded-full bg-grade-a"></span>
             MIC_STAT: OK
          </span>
          <span className="flex items-center gap-1">
             <span className="w-2 h-2 rounded-full bg-grade-a"></span>
             CAM_STAT: OK
          </span>
        </div>
        <span className="text-off-white">SEQ: {scanPhase + 1}/4</span>
      </div>
    </div>
  )
}

export default function IndustrialHero() {
  return (
    <section className="relative min-h-screen pt-28 pb-20 px-4 md:px-8 bg-ind-dark flex flex-col justify-between overflow-hidden text-off-white font-sans">
      <div className="max-w-7xl mx-auto w-full space-y-16 relative z-10">
        
        {/* Top Hardware Banner Badge */}
        <div className="inline-flex items-center gap-3 px-4 py-2 bg-ind-panel border border-ind-border">
          <span className="w-2.5 h-2.5 bg-raf-blue animate-pulse-slow" />
          <span className="font-mono text-xs font-bold text-text-muted uppercase">
            SEC-01 // SYSTEM SPECIFICATION
          </span>
        </div>

        {/* Hero Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          <div className="lg:col-span-6 space-y-6">
            <h1 className="text-5xl md:text-7xl font-bold uppercase tracking-tight leading-[0.9]">
              QUALITY SIGNALS <br />
              <span className="text-raf-blue">BEYOND THE SURFACE.</span>
            </h1>

            <p className="text-lg text-text-muted max-w-xl border-l-2 border-ind-border pl-4">
              Controlled acoustic response and calibrated RGB vision for evidence-led onion procurement screening.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-4">
              <button className="flex items-center gap-2 px-6 py-3 bg-raf-blue text-ind-dark font-bold tracking-widest uppercase text-sm hover:bg-blue-400 transition-colors">
                <Power size={16} /> START INSPECTION
              </button>

              <Link to="/prototype" className="flex items-center gap-2 px-6 py-3 border border-ind-border text-off-white font-bold tracking-widest uppercase text-sm hover:bg-ind-panel transition-colors">
                VIEW TEST BENCH <ArrowRight size={16} />
              </Link>
            </div>

            {/* Spec Output */}
            <div className="grid grid-cols-3 gap-4 pt-8 border-t border-ind-border font-mono text-xs mt-8">
              <div>
                <span className="text-text-muted block text-[10px] uppercase">Acoustic range</span>
                <span className="font-bold text-off-white">100Hz – 2.5kHz</span>
              </div>
              <div>
                <span className="text-text-muted block text-[10px] uppercase">System status</span>
                <span className="font-bold text-grade-a flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-grade-a animate-pulse" />
                  ONLINE
                </span>
              </div>
              <div>
                <span className="text-text-muted block text-[10px] uppercase">Inspection rate</span>
                <span className="font-bold text-raf-blue">1.2s / UNIT</span>
              </div>
            </div>
          </div>

          {/* Right Schematic Visual */}
          <div className="lg:col-span-6">
            <TechnicalSchematic />
          </div>
        </div>

        {/* Embedded Interactive Inspector (Optional based on design requirements, kept to avoid removing core functionality) */}
        <div className="pt-16 border-t border-ind-border">
          <div className="mb-4 flex items-center gap-2 font-mono text-xs text-text-muted">
             <span className="bg-ind-border px-2 py-0.5 text-off-white">02</span>
             MANUAL CROSS-SECTION REVIEW
          </div>
          <OnionLayerInspector />
        </div>
      </div>
    </section>
  )
}
