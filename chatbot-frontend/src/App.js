import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import Home from './pages/Home';  // Also confirm this path
import NotFound from './pages/NotFound';
import ServerError from './pages/ServerError';
import DatabaseError from './pages/DatabaseError';


function App() {
  return (
    
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="*" element={<NotFound />} />
          <Route path="/500" element={<ServerError />} />
          <Route path="/db-error" element={
          <DatabaseError 
            db_host="localhost" 
            db_name="mydb" 
            db_user="admin" 
            db_port="5432" 
            db_sslmode="disable" 
            error_message="Connection refused: Check if the database server is running." 
          />
        } />
        </Routes>
      </Router>
   
  );
}

export default App;
