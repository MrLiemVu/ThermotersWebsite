import React, { useState, useEffect } from 'react';
import { collection, query, orderBy, getDocs } from 'firebase/firestore';
import { db } from '../../firebaseConfig'; // Import your Firebase config
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  TablePagination, TableSortLabel, Paper, Box, Typography, Modal 
} from '@mui/material';
import { getAuth } from 'firebase/auth';

const HistoryTable = () => {
  const [jobs, setJobs] = useState([]);
  const [order, setOrder] = useState('asc');
  const [orderByColumn, setOrderByColumn] = useState('jobName');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [openModal, setOpenModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const auth = getAuth();

  // Fetch data from Firestore
  useEffect(() => {
    const fetchJobs = async () => {
      if (!auth.currentUser) return; // Don't fetch if not logged in

      try {
        const userJobsRef = collection(db, "users", auth.currentUser.uid, "jobhistory");
        const q = query(userJobsRef, orderBy("uploadedAt", "desc"));
        const querySnapshot = await getDocs(q);
        const jobData = querySnapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }));
        setJobs(jobData);
      } catch (error) {
        console.error("Error fetching jobs:", error);
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

  return (
    <Box>
      <TableContainer component={Paper}>
        <Table aria-label="job table">
          <TableHead>
            <TableRow>
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
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((job) => (
              <TableRow key={job.id} onClick={() => handleRowClick(job)} style={{ cursor: 'pointer' }}>
                <TableCell>{job.jobName}</TableCell>
                <TableCell>{new Date(job.uploadedAt.seconds * 1000).toLocaleDateString()}</TableCell>
                <TableCell>{job.results}</TableCell>
                <TableCell>{job.status}</TableCell>
              </TableRow>
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