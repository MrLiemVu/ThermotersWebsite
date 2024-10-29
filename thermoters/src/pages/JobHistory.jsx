import React from 'react';
import { Box, Typography, Divider } from '@mui/material';
import HistoryTable from '../components/HistoryTable'; // Import the HistoryTable component

const JobHistoryPage = () => {
  return (
    <Box
      sx={{
        mx: 'auto',
        mt: 1,
        p: 3,
      }}
    >
      {/* Title */}
      <Typography variant="h4" component="h1" gutterBottom>
        Job History
      </Typography>

      {/* Subtitle/Description */}
      <Typography variant="body1" paragraph>
        Below is a history of your submitted jobs. You can view the details of each job, check the status, and see the results.
        Click on any job to see more detailed information.
      </Typography>

      {/* Divider for visual separation */}
      <Divider sx={{ my: 2 }} />

      {/* Job History Table */}
      <HistoryTable />
    </Box>
  );
};

export default JobHistoryPage;