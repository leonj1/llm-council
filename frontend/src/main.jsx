import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import LandingPage from './pages/LandingPage.jsx'
import MemoriesPage from './pages/MemoriesPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/chat" element={<App />} />
        <Route path="/chat/:conversationId" element={<App />} />
        <Route path="/memories" element={<MemoriesPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
