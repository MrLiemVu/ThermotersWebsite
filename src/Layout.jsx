// src/Layout.js
import React from 'react';
import { Box } from '@mui/material';
import NavRail from './components/Navrail';

const Layout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex' }}>
      {/* Navigation Rail */}
      <NavRail />

      {/* Main Content */}
      <Box 
        component="main"
        sx={{ 
          marginLeft: '240px', // Width of NavRail
          width: 'calc(100% - 240px)',
          minHeight: '100vh',
          p: { xs: 3, sm: 10 }, // Reduced padding to prevent content getting pushed down
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}
      >
        <Box sx={{ 
          width: '100%',
          maxWidth: '1600px',
          mx: 'auto',
          px: { xs: 2, sm: 15 }, // Reduced horizontal padding
        }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;