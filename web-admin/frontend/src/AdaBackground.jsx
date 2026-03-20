import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import NET from 'vanta/dist/vanta.net.min'

export const AdaBackground = () => {
  const [vantaEffect, setVantaEffect] = useState(null)
  const myRef = useRef(null)

  useEffect(() => {
    if (!vantaEffect) {
      setVantaEffect(
        NET({
          el: myRef.current,
          THREE: THREE,
          color: 0x0b74ff,     // ADA Accent color (Blue)
          backgroundColor: 0x050814, // Deep dark background
          points: 12.00,
          maxDistance: 22.00,
          spacing: 16.00,
          showDots: true
        })
      )
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy()
    }
  }, [vantaEffect])

  return (
    <div
      ref={myRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1, // Ensure it stays behind all content
        pointerEvents: 'none' // Don't block clicks on the actual UI
      }}
    />
  )
}
