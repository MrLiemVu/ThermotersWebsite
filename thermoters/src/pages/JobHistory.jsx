import React from 'react';
import { Box, Typography, Divider } from '@mui/material';
import HistoryTable from '../components/HistoryTable';

const JobHistoryPage = () => {
  return (
    <Box sx={{ width: '100%' }}>
      {/* Title Section */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="bold" gutterBottom>
          Job History
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Below is a history of your submitted jobs. You can view the details of each job, check the status, and see the results.
          Click on any job to see more detailed information.
        </Typography>
      </Box>

      {/* Divider for visual separation */}
      <Divider sx={{ my: 3 }} />

      <Typography variant="body2" color="text.secondary">
        <strong>WARNING:</strong> Jobs will be saved for 6 months before deletion from our servers.
      </Typography>

      {/* Job History Table */}
      <Box sx={{ width: '100%' }}>
        <HistoryTable />
      </Box>
    </Box>
  );
};

export default JobHistoryPage;