// NavRail.js
import React from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Divider } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import ScienceIcon from '@mui/icons-material/Science';
import HistoryIcon from '@mui/icons-material/History';
import LoginIcon from '@mui/icons-material/Login';
import { Link } from 'react-router-dom';

const NavRail = () => {
  return (
    <Box
      sx={{
        width: 240,
        height: '100vh', // Make it span the full screen height
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f3f4f6',
        p: 2,
        boxShadow: 3,
        position: 'fixed', // Fixes it to the side of the screen
      }}
    >
      <Typography variant="h6" align="center" gutterBottom>
        Gene Expression Predictor
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <List>
        <ListItem disablePadding>
          <ListItemButton
            component={Link}
            to="/"
            sx={{
              '&:hover': {
                backgroundColor: '#e0e0e0', // Hover color
              },
              gap: 1, // Adjust spacing between icon and text
              borderRadius: 1, // Optional: for rounded corners on hover
              px: 2, // Optional padding for visual balance
            }}
          >
            <ListItemIcon sx={{ minWidth: '40px' }}>
              <HomeIcon />
            </ListItemIcon>
            <ListItemText primary="Home" />
          </ListItemButton>
        </ListItem>

        <ListItem disablePadding>
          <ListItemButton
            component={Link}
            to="/algorithms"
            sx={{
              '&:hover': {
                backgroundColor: '#e0e0e0',
              },
              gap: 1,
              borderRadius: 1,
              px: 2,
            }}
          >
            <ListItemIcon sx={{ minWidth: '40px' }}>
              <ScienceIcon />
            </ListItemIcon>
            <ListItemText primary="Algorithms" />
          </ListItemButton>
        </ListItem>

        <ListItem disablePadding>
          <ListItemButton
            component={Link}
            to="/history"
            sx={{
              '&:hover': {
                backgroundColor: '#e0e0e0',
              },
              gap: 1,
              borderRadius: 1,
              px: 2,
            }}
          >
            <ListItemIcon sx={{ minWidth: '40px' }}>
              <HistoryIcon />
            </ListItemIcon>
            <ListItemText primary="History" />
          </ListItemButton>
        </ListItem>

        <Divider sx={{ my: 2 }} />

        <ListItem disablePadding>
          <ListItemButton
            component={Link}
            to="/login"
            sx={{
              '&:hover': {
                backgroundColor: '#e0e0e0',
              },
              gap: 1,
              borderRadius: 1,
              px: 2,
            }}
          >
            <ListItemIcon sx={{ minWidth: '40px' }}>
              <LoginIcon />
            </ListItemIcon>
            <ListItemText primary="Login" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );
};

export default NavRail;
