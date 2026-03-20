import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import AppV2 from './AppV2'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {window.location.pathname.startsWith('/v2') ? <AppV2 /> : <App />}
  </React.StrictMode>
)
