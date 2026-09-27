import CinematicHero from '../sections/CinematicHero'
import CoreStorySequence from '../sections/CoreStorySequence'
import FFTVisualization from '../sections/FFTVisualization'
import InternalStructureExplorer from '../sections/InternalStructureExplorer'
import LMSDashboard from '../sections/LMSDashboard'
import FooterCTA from '../sections/FooterCTA'

export default function Home() {
  return (
    <div className="bg-bg-base min-h-screen text-text-primary selection:bg-onion/15">
      <main>
        <CinematicHero />
        <CoreStorySequence />
        <FFTVisualization />
        <InternalStructureExplorer />
        <LMSDashboard />
        <FooterCTA />
      </main>
    </div>
  )
}
