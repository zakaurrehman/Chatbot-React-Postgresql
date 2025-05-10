import React from 'react';

const ServerError = () => {
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
    color: '#dc3545',
    marginBottom: '1rem'
  };

  const errorTextStyle = {
    fontSize: '1.5rem',
    marginBottom: '2rem'
  };

  const paragraphStyle = {
    marginBottom: '1.5rem'
  };

  const buttonStyle = {
    backgroundColor: '#0d6efd',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '0.25rem',
    color: 'white',
    textDecoration: 'none'
  };

  return (
    <div style={bodyStyle}>
      <div style={errorContainerStyle}>
        <div style={errorCodeStyle}>500</div>
        <div style={errorTextStyle}>Server Error</div>
        <p style={paragraphStyle}>Something went wrong on our end. Please try again later.</p>
        <a href="/" style={buttonStyle}>Return to Home</a>
      </div>
    </div>
  );
};

export default ServerError;
