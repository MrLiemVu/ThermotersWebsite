// AlgorithmsPage.js
import React from 'react';
import { Box, Typography } from '@mui/material';
import AlgoForm from '../components/AlgoForm';

const AlgorithmsPage = () => {
  return (
    <Box sx={{ width: '100%', mt: 2 }}>
      {/* Title and Subtitle */}
      <Box sx={{ 
        textAlign: 'center', 
        mb: 4,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <Typography 
          variant="h3" 
          fontWeight="bold" 
          gutterBottom
          sx={{ display: 'block' }}
        >
          Algorithms
        </Typography>
        <Typography 
          variant="h6" 
          color="textSecondary"
          sx={{ display: 'block' }}
        >
          Gene Expression Predictor
        </Typography>
      </Box>

      {/* Form Section */}
      <AlgoForm />
    </Box>
  );
};

export default AlgorithmsPage;