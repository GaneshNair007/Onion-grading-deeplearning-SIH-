import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function FooterCTA() {
  return (
    <section className="relative py-32 bg-bg-base overflow-hidden">
      {/* Background decor */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-onion-soft/40 rounded-full blur-[160px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: false, amount: 0.2 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="max-w-4xl mx-auto px-6 text-center relative z-10"
      >
        <div className="section-label mb-6">Explore the system</div>
        <h2 className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-6">
          Ready to explore <span className="">Go further.</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-xl mx-auto mb-10 leading-relaxed">
          Explore the working prototype, understand the technical approach, or connect with the team building the system.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/prototype" className="btn-onion">
            Open the Prototype Lab <ArrowRight size={16} />
          </Link>
          <Link to="/about" className="btn-premium">
            About the Project <ArrowRight size={14} />
          </Link>
        </div>
      </motion.div>


    </section>
  )
}
