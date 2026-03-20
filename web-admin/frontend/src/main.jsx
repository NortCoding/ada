import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import AppV2 from './AppV2'
import AppV1 from './AppV1'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<AppV1 />} />
        <Route path="/v2/*" element={<AppV2 />} />

      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
