import React, { useState, useEffect } from 'react';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setData({
        message: 'Hello from React Multi-Stage Build!',
        timestamp: new Date().toISOString(),
        buildTime: process.env.REACT_APP_BUILD_TIME || 'unknown'
      });
    }, 1000);
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>React Multi-Stage Build Demo</h1>
      {data ? (
        <div>
          <p><strong>Message:</strong> {data.message}</p>
          <p><strong>Current Time:</strong> {data.timestamp}</p>
          <p><strong>Build Time:</strong> {data.buildTime}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default App;
