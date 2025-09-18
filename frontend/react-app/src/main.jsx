import React from 'react'
import ReactDOM from 'react-dom/client'

// Simple test component
function App() {
  return (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontFamily: 'Arial, sans-serif',
      textAlign: 'center'
    }}>
      <div style={{
        background: 'rgba(255,255,255,0.95)',
        color: '#333',
        padding: '40px',
        borderRadius: '20px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ fontSize: '3rem', margin: '0 0 20px 0' }}>
          🎨 VastraVista
        </h1>
        <p style={{ fontSize: '1.5rem', margin: '0 0 10px 0' }}>
          AI Fashion Recommendation System
        </p>
        <p style={{ fontSize: '1.2rem', color: '#666' }}>
          👨‍🎓 By Saumya Tiwari | B.Tech CSE Final Year
        </p>
        <div style={{
          background: '#e8f5e8',
          padding: '20px',
          borderRadius: '10px',
          margin: '20px 0',
          color: '#2d5a2d'
        }}>
          <strong>✅ React Frontend Working!</strong><br/>
          Your web interface is ready for AI integration.
        </div>
        <button 
          onClick={() => {
            fetch('http://localhost:5001/api/health')
              .then(res => res.json())
              .then(data => alert('🎉 Backend Status: ' + JSON.stringify(data.modules)))
              .catch(err => alert('❌ Backend not running on port 5001'))
          }}
          style={{
            background: '#667eea',
            color: 'white',
            border: 'none',
            padding: '15px 30px',
            borderRadius: '10px',
            fontSize: '1.1rem',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          🔗 Test Backend Connection
        </button>
      </div>
    </div>
  )
}

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)

console.log('🚀 VastraVista loaded successfully!')
