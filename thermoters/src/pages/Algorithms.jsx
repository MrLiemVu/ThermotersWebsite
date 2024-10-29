// AlgorithmsPage.js
import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import AlgoForm from '../components/AlgoForm'; // Import the AlgoForm component

const AlgorithmsPage = () => {
  return (
    <Box
      sx={{
        mx: 'auto',
        mt: 4,
        p: 3,
      }}
    >
      {/* Title and Subtitle */}
      <Box textAlign="center" mb={4}>
        <Typography variant="h4" fontWeight="bold">
          Algorithms
        </Typography>
        <Typography variant="h6" color="textSecondary">
          Gene Expression Predictor
        </Typography>
      </Box>

      {/* Form Section */}
      <AlgoForm />
      
      {/* Instructions Section */}
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Paper
          elevation={3}
          sx={{
            mt: 4,
            p: 3,
            backgroundColor: '#f3e5f5',
            borderRadius: 2,
            maxWidth: '50%'
          }}
        >
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            How to use
          </Typography>
          <Typography variant="body2" mb={2}>
            Input sequence then choose the algorithm for predicting expression levels. Select if you want predictions on the
            'forward' strand (input sequence from left to right), 'reverse complement' or both. Note that the first upstream
            35 base pairs in the sequence cannot be evaluated (due to the minimum binding site length of sigma70), so
            include at least 35bp upstream of your sequence of interest (these can also be a string of Gs to help interpretation).
          </Typography>
          <Typography variant="body2">
            The output includes the brick plot and the predicted expression level (Pon). Registered users can input up to 100 sequences.
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default AlgorithmsPage;