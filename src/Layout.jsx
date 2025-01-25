// src/Layout.js
import React, { useEffect } from 'react';
import { Box } from '@mui/material';
import NavRail from './components/Navrail';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { Outlet } from 'react-router-dom';

const Layout = () => {
  const location = useLocation();

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
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Outlet />
          </motion.div>
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;