import React, { useState, useEffect } from 'react';
import { collection, query, orderBy, getDocs, doc } from 'firebase/firestore';
import { db } from '../../firebaseConfig'; // Import your Firebase config
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  TablePagination, TableSortLabel, Paper, Box, Typography, Modal, IconButton, Collapse, Button 
} from '@mui/material';
import { getAuth } from 'firebase/auth';
import { KeyboardArrowDown, KeyboardArrowUp, Download } from '@mui/icons-material';
import '../styles/HistoryTable.css';  // Adjust path based on your structure

const HistoryTable = () => {
  const [jobs, setJobs] = useState([]);
  const [order, setOrder] = useState('asc');
  const [orderByColumn, setOrderByColumn] = useState('jobName');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [openModal, setOpenModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);
  const auth = getAuth();

  // Fetch data from Firestore
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const user = auth.currentUser;
        if (!user) return;
        
        // Generate document ID from email/uid
        const sanitizedEmail = user.email
          .replace(/@/g, '_at_')
          .replace(/\./g, '_dot_')
          .replace(/[^a-zA-Z0-9_-]/g, '');
        const docId = `${sanitizedEmail}-${user.uid}`;

        const userDocRef = doc(db, "users", docId);
        const jobsRef = collection(userDocRef, "jobs");
        const q = query(jobsRef, orderBy("createdAt", "desc"));
        const querySnapshot = await getDocs(q);
        const jobData = querySnapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
          createdAt: doc.data().createdAt?.toDate() || new Date()
        }));
        setJobs(jobData);
      } catch (error) {
        console.error("Error fetching jobs:", error);
        if (error.code === 'permission-denied') {
          console.error('Firestore rules blocking access. Verify:');
          console.error('1. User is authenticated');
          console.error('2. Document userId matches auth uid');
          console.error('3. Rules are deployed correctly');
        }
      }
    };

    fetchJobs();
  }, [auth.currentUser]); // Re-fetch when user changes

  // Sorting handler
  const handleRequestSort = (property) => {
    const isAscending = orderByColumn === property && order === 'asc';
    setOrder(isAscending ? 'desc' : 'asc');
    setOrderByColumn(property);
    const sortedJobs = [...jobs].sort((a, b) => {
      if (a[property] < b[property]) return order === 'asc' ? -1 : 1;
      if (a[property] > b[property]) return order === 'asc' ? 1 : -1;
      return 0;
    });
    setJobs(sortedJobs);
  };

  // Pagination handlers
  const handleChangePage = (event, newPage) => setPage(newPage);
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Row click handler for modal
  const handleRowClick = (job) => {
    setSelectedJob(job);
    setOpenModal(true);
  };

  const handleDownloadJson = (job) => {
    const jsonString = JSON.stringify(job, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `job-${job.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // When viewing historical job
  const regeneratePlot = async (jobParams) => {
    const response = await fetch('/submit_job', {
      method: 'POST',
      body: JSON.stringify(jobParams)
    });
    return await response.json();
  };

  return (
    <Box>
      <TableContainer component={Paper} sx={{ mt: 4 }}>
        <Table aria-label="job history table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell sortDirection={orderByColumn === 'jobName' ? order : false}>
                <TableSortLabel
                  active={orderByColumn === 'jobName'}
                  direction={orderByColumn === 'jobName' ? order : 'asc'}
                  onClick={() => handleRequestSort('jobName')}
                >
                  Job Name
                </TableSortLabel>
              </TableCell>
              <TableCell sortDirection={orderByColumn === 'uploadedAt' ? order : false}>
                <TableSortLabel
                  active={orderByColumn === 'uploadedAt'}
                  direction={orderByColumn === 'uploadedAt' ? order : 'asc'}
                  onClick={() => handleRequestSort('uploadedAt')}
                >
                  Date
                </TableSortLabel>
              </TableCell>
              <TableCell>Results</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((job) => (
              <React.Fragment key={job.id}>
                <TableRow 
                  sx={{ '& > *': { borderBottom: 'unset' } }}
                  onClick={() => setExpandedRow(expandedRow === job.id ? null : job.id)}
                >
                  <TableCell>
                    <IconButton size="small">
                      {expandedRow === job.id ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
                    </IconButton>
                  </TableCell>
                  <TableCell component="th" scope="row">
                    {job.jobName}
                  </TableCell>
                  <TableCell>{new Date(job.uploadedAt.seconds * 1000).toLocaleDateString()}</TableCell>
                  <TableCell>{job.results}</TableCell>
                  <TableCell>{job.status}</TableCell>
                  <TableCell align="right">
                    <Button 
                      variant="outlined" 
                      startIcon={<Download />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownloadJson(job);
                      }}
                    >
                      JSON
                    </Button>
                  </TableCell>
                </TableRow>
                
                <TableRow>
                  <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                    <Collapse in={expandedRow === job.id} timeout="auto" unmountOnExit>
                      <Box sx={{ margin: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Job Details
                        </Typography>
                        
                        <div style={{ display: 'flex', gap: '2rem' }}>
                          {/* Job Parameters */}
                          <div style={{ flex: 1 }}>
                            <Typography variant="subtitle1">Parameters:</Typography>
                            <pre style={{ 
                              backgroundColor: '#f5f5f5',
                              padding: '1rem',
                              borderRadius: '4px',
                              maxHeight: '300px',
                              overflow: 'auto'
                            }}>
                              {JSON.stringify({
                                sequence: job.sequence,
                                predictors: job.predictors,
                                // Add other parameters here
                              }, null, 2)}
                            </pre>
                          </div>

                          {/* Visualization */}
                          {job.results.image && (
                            <div style={{ flex: 1 }}>
                              <Typography variant="subtitle1" gutterBottom>
                                Visualization
                              </Typography>
                              <img 
                                src={`data:image/png;base64,${job.results.image}`} 
                                alt="Brickplot visualization"
                                style={{ maxWidth: '100%', height: 'auto' }}
                              />
                              <Button
                                variant="contained"
                                sx={{ mt: 1 }}
                                href={job.results.image}
                                download={`job-${job.id}.png`}
                              >
                                Download Image
                              </Button>
                            </div>
                          )}
                        </div>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={jobs.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      {/* Modal for more details */}
      <Modal open={openModal} onClose={() => setOpenModal(false)}>
        <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', p: 4, borderRadius: 2, boxShadow: 24 }}>
          {selectedJob && (
            <>
              <Typography variant="h6" component="h2">{selectedJob.jobName}</Typography>
              <Typography variant="body2">Date: {new Date(selectedJob.uploadedAt.seconds * 1000).toLocaleString()}</Typography>
              <Typography variant="body2">Results: {selectedJob.results}</Typography>
              <Typography variant="body2">Status: {selectedJob.status}</Typography>
            </>
          )}
        </Box>
      </Modal>
    </Box>
  );
};

export default HistoryTable;