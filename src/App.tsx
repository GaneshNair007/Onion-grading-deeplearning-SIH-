import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import SiteNav from './components/SiteNav'
import Footer from './components/Footer'
import Home from './pages/Home'
import About from './pages/About'
import Prototype from './pages/Prototype'

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className="flex flex-col min-h-screen">
        <SiteNav />
        <main className="flex-grow">
          <Routes>
            <Route path="/"          element={<Home />} />
            <Route path="/about"     element={<About />} />
            <Route path="/prototype" element={<Prototype />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}
