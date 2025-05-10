import React from 'react';

const NotFound = () => {
  const bodyStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    backgroundColor: '#f8f9fa'
  };

  const errorContainerStyle = {
    textAlign: 'center',
    padding: '2rem',
    backgroundColor: 'white',
    borderRadius: '10px',
    boxShadow: '0 0 20px rgba(0, 0, 0, 0.1)',
    maxWidth: '500px'
  };

  const errorCodeStyle = {
    fontSize: '6rem',
    fontWeight: '700',
    color: '#0d6efd',
    marginBottom: '1rem'
  };

  const errorTextStyle = {
    fontSize: '1.5rem',
    marginBottom: '2rem'
  };

  const buttonStyle = {
    backgroundColor: '#0d6efd',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '0.25rem',
    color: 'white',
    textDecoration: 'none'
  };

  const paragraphStyle = {
    marginBottom: '1.5rem'
  };

  return (
    <div style={bodyStyle}>
      <div style={errorContainerStyle}>
        <div style={errorCodeStyle}>404</div>
        <div style={errorTextStyle}>Page Not Found</div>
        <p style={paragraphStyle}>The page you are looking for does not exist or has been moved.</p>
        <a href="/" style={buttonStyle}>Return to Home</a>
      </div>
    </div>
  );
};

export default NotFound;
