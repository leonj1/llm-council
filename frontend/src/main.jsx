import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './ThemeContext.jsx'
import { ToastProvider } from './components/Toast.jsx'
import './index.css'
import App from './App.jsx'
import LandingPage from './pages/LandingPage.jsx'
import MemoriesPage from './pages/MemoriesPage.jsx'
import CrawlerPage from './pages/CrawlerPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/chat" element={<App />} />
            <Route path="/chat/:conversationId" element={<App />} />
            <Route path="/memories" element={<MemoriesPage />} />
            <Route path="/crawler" element={<CrawlerPage />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)
