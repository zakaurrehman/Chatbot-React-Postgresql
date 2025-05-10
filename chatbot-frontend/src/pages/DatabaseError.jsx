import React from 'react';

const DatabaseError = ({ db_host, db_name, db_user, db_port, db_sslmode, error_message }) => {
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
    maxWidth: '700px'
  };

  const errorIconStyle = {
    fontSize: '4rem',
    color: '#dc3545',
    marginBottom: '1rem'
  };

  const errorTitleStyle = {
    fontSize: '2rem',
    marginBottom: '1rem'
  };

  const connectionDetailsStyle = {
    textAlign: 'left',
    backgroundColor: '#f8f9fa',
    padding: '1rem',
    borderRadius: '5px',
    margin: '1rem 0'
  };

  const alertStyle = {
    backgroundColor: '#f8d7da',
    color: '#842029',
    padding: '1rem',
    borderRadius: '5px',
    marginTop: '1rem',
    border: '1px solid #f5c2c7'
  };

  const buttonPrimaryStyle = {
    backgroundColor: '#0d6efd',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '0.25rem',
    color: 'white',
    textDecoration: 'none',
    marginRight: '0.5rem'
  };

  const buttonSecondaryStyle = {
    border: '1px solid #6c757d',
    padding: '0.5rem 1rem',
    borderRadius: '0.25rem',
    color: '#6c757d',
    backgroundColor: 'transparent',
    cursor: 'pointer'
  };

  return (
    <div style={bodyStyle}>
      <div style={errorContainerStyle}>
        <div style={errorIconStyle}>
          <i className="bi bi-database-x"></i>
        </div>
        <div style={errorTitleStyle}>Database Connection Error</div>
        <p>Unable to connect to the PostgreSQL database. Please check your database configuration.</p>

        <div style={connectionDetailsStyle}>
          <h5>Connection Details:</h5>
          <ul>
            <li><strong>Host:</strong> {db_host}</li>
            <li><strong>Database:</strong> {db_name}</li>
            <li><strong>User:</strong> {db_user}</li>
            <li><strong>Port:</strong> {db_port}</li>
            <li><strong>SSL Mode:</strong> {db_sslmode}</li>
          </ul>
        </div>

        <div style={alertStyle}>
          {error_message}
        </div>

        <p>Please check your database credentials in the .env file and ensure your database server is accessible.</p>

        <div style={{ marginTop: '1.5rem' }}>
          <a href="/" style={buttonPrimaryStyle}>Try Again</a>
          <button style={buttonSecondaryStyle} onClick={() => window.history.back()}>Go Back</button>
        </div>
      </div>
    </div>
  );
};

export default DatabaseError;
