import { motion, useScroll, useTransform } from 'framer-motion'
import { ArrowRight, ArrowDown } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function CinematicHero() {
  const { scrollY } = useScroll()
  const bgY = useTransform(scrollY, [0, 800], ['0%', '12%'])
  const textY = useTransform(scrollY, [0, 800], ['0%', '30%'])
  const opacity = useTransform(scrollY, [0, 500], [1, 0])

  return (
    <section className="relative w-full h-screen overflow-hidden bg-bg-base flex items-center justify-center">
      
      {/* Background Video + Overlays */}
      <motion.div style={{ y: bgY }} className="absolute inset-0 z-0">
        <video
          autoPlay loop muted playsInline
          className="absolute inset-0 w-full h-full object-cover object-[75%_center]"
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
      </motion.div>

      {/* Decorative floating circles */}
      <div className="absolute top-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-onion-light/30 blur-[100px] pointer-events-none animate-float" />
      <div className="absolute bottom-1/3 left-1/4 w-[250px] h-[250px] rounded-full bg-pastel-lavender/30 blur-[80px] pointer-events-none animate-float" style={{ animationDelay: '2s' }} />

      {/* Water Splash Effect at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-20 water-splash pointer-events-none z-30" />
      
      {/* Water ripple circles */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 pointer-events-none z-20">
        <div className="water-ripple" style={{ animationDelay: '0s' }} />
        <div className="water-ripple" style={{ animationDelay: '1s' }} />
        <div className="water-ripple" style={{ animationDelay: '2s' }} />
      </div>

      {/* Main Content */}
      <motion.div
        style={{ y: textY, opacity }}
        className="relative z-20 flex flex-col items-start text-left px-8 md:px-16 max-w-7xl w-full mx-auto"
      >

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 40, filter: 'blur(12px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ delay: 0.6, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl md:text-7xl lg:text-[90px] font-display font-semibold tracking-tight leading-[1.05] text-text-primary mb-8 max-w-4xl"
        >
          See Beyond <span className="">the Surface.</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0, duration: 0.8 }}
          className="text-lg md:text-xl text-text-secondary font-sans font-normal max-w-xl mb-4 leading-relaxed"
        >
          Non-destructive onion quality grading powered by
          acoustic intelligence and machine learning.
        </motion.p>


        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5, duration: 0.8 }}
          className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mt-2"
        >
          <Link to="/about" className="btn-onion">
            Discover the Technology
            <ArrowRight size={16} />
          </Link>
          <Link to="/prototype" className="btn-premium">
            Explore the Lab
            <ArrowRight size={14} />
          </Link>
        </motion.div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.5, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-40 flex flex-col items-center gap-2"
      >
        <span className="text-[10px] font-sans font-medium text-text-muted tracking-[0.2em] uppercase">Scroll</span>
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <ArrowDown size={14} className="text-onion/50" />
        </motion.div>
      </motion.div>
    </section>
  )
}
