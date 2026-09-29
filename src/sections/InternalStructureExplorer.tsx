import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

const layers = [
  {
    id: 'detection',
    name: 'Object Detection & Segmentation',
    desc: 'The YOLO vision model identifies each individual onion in a single tray, placing precise bounding boxes and segmentation masks around them.',
    color: '#D4687A',
    size: 'w-72 h-72',
    borderW: 'border',
  },
  {
    id: 'sizing',
    name: 'Calibrated Size Measurement',
    desc: 'Using an in-frame calibration reference, the system calculates exact pixel-to-mm ratio, ensuring "undersized" is a real measurement, not a guess.',
    color: '#D4687A',
    size: 'w-56 h-56',
    borderW: 'border-2',
  },
  {
    id: 'defects',
    name: 'Surface Defect Classification',
    desc: 'The model analyzes the visible surface to flag damage, rot, and sprouting with dedicated confidence scores for every onion.',
    color: '#D4687A',
    size: 'w-40 h-40',
    borderW: 'border-2 border-dashed',
  },
  {
    id: 'rules',
    name: 'Configurable Rule Engine',
    desc: 'Measurements are passed through an active procurement policy to automatically calculate batch percentages and generate digital reports.',
    color: '#D4687A',
    size: 'w-20 h-20',
    borderW: 'border-2',
  },
]

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
}

export default function InternalStructureExplorer() {
  const [activeLayer, setActiveLayer] = useState<string>('detection')
  const [isUserHovering, setIsUserHovering] = useState<boolean>(false)

  // Auto-cycle through layers in a continuous loop unless user is hovering
  useEffect(() => {
    if (isUserHovering) return
    const interval = setInterval(() => {
      setActiveLayer((current) => {
        const idx = layers.findIndex((l) => l.id === current)
        const nextIdx = (idx + 1) % layers.length
        return layers[nextIdx].id
      })
    }, 3200)
    return () => clearInterval(interval)
  }, [isUserHovering])

  return (
    <section className="relative w-full py-32 bg-bg-blush overflow-hidden">
      {/* Background atmosphere */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-onion-soft/50 blur-[160px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          
          {/* Left: Text & Layer Controls */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: false, amount: 0.2 }}
            variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.12 } } }}
            className="flex flex-col gap-10"
          >
            <div>
              <motion.div variants={fadeUp} className="section-label mb-4">Vision Pipeline</motion.div>
              <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-6">
                Primary <span className="italic">Optical Grading</span>
              </motion.h2>
              <motion.p variants={fadeUp} className="text-base text-text-secondary leading-relaxed">
                Hover over each step to see how our computer vision pipeline processes images into actionable, calibrated quality metrics.
              </motion.p>
            </div>

            {/* Layer Controls */}
            <motion.div variants={fadeUp} className="flex flex-col gap-1 relative">
              {/* Vertical timeline line */}
              <div className="absolute left-3 top-6 bottom-6 w-px bg-onion-light/60" />
              
              {layers.map((layer) => {
                const active = activeLayer === layer.id
                return (
                  <div
                    key={layer.id}
                    className={`relative pl-10 py-4 rounded-2xl cursor-pointer transition-all duration-400 ${
                      active ? 'bg-onion-soft/60' : 'hover:bg-onion-soft/30'
                    }`}
                    onMouseEnter={() => {
                      setActiveLayer(layer.id)
                      setIsUserHovering(true)
                    }}
                    onMouseLeave={() => {
                      setIsUserHovering(false)
                    }}
                  >
                    {/* Timeline dot */}
                    <div className={`absolute left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full transition-all duration-400 ${
                      active
                        ? 'bg-onion shadow-[0_0_12px_rgba(212,104,122,0.5)] scale-125'
                        : 'bg-onion-light border border-onion/20'
                    }`} />

                    <h4 className={`font-display text-lg font-semibold transition-colors duration-300 mb-1 ${
                      active ? 'text-onion-deep' : 'text-text-primary'
                    }`}>
                      {layer.name}
                    </h4>
                    <p className={`text-sm font-sans leading-relaxed transition-all duration-300 ${
                      active ? 'text-text-secondary opacity-100' : 'text-text-muted opacity-70'
                    }`}>
                      {layer.desc}
                    </p>
                  </div>
                )
              })}
            </motion.div>
          </motion.div>

          {/* Right: Computer Vision Video Visualizer with looping scan beam */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: false, amount: 0.2 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            animate={{
              boxShadow: [
                '0 8px 30px rgba(212, 104, 122, 0.12)',
                '0 8px 45px rgba(212, 104, 122, 0.28)',
                '0 8px 30px rgba(212, 104, 122, 0.12)',
              ],
            }}
            className="relative h-[420px] flex items-center justify-center rounded-3xl overflow-hidden border border-glass-border"
          >
            {/* Looping Frame Motion Scan Beam */}
            <motion.div
              animate={{
                top: ['2%', '96%', '2%'],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-onion to-transparent shadow-[0_0_12px_#D4687A] z-20 pointer-events-none"
            />
            <video
              autoPlay
              muted
              loop
              playsInline
              className="w-full h-full object-cover"
            >
              <source src="/opencv.mp4" type="video/mp4" />
            </video>
            {/* Optional gradient overlay to match aesthetic */}
            <div className="absolute inset-0 bg-gradient-to-t from-bg-base/20 to-transparent pointer-events-none" />
          </motion.div>
        </div>
      </div>
    </section>
  )
}
