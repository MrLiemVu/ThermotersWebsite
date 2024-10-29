// src/Layout.js
import React from 'react';
import { Box } from '@mui/material';
import NavRail from './components/NavRail';

const Layout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex' }}>
      {/* Navigation Rail */}
      <NavRail />

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, ml: '240px', width: '100%' }}>
        {children}
      </Box>
    </Box>
  );
};

export default Layout;