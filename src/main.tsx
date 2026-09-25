import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthContext'
import { ClinicalDataProvider } from './clinical/ClinicalDataContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>    {/* Added BrowserRouter around App to provide routing context for useNavigate() */}
      <AuthProvider>    {/* Added AuthProvider around App to provide authentication context for useAuth() */}
        <ClinicalDataProvider>    {/* Added ClinicalDataProvider around App to provide clinical data context for useClinicalData() */}
        <App />
        </ClinicalDataProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)