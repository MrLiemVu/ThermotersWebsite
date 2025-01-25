// NavRail.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Divider, CircularProgress } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import ScienceIcon from '@mui/icons-material/Science';
import HistoryIcon from '@mui/icons-material/History';
import LoginIcon from '@mui/icons-material/Login';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import { Link } from 'react-router-dom';
import LoginModal from './LoginModal';
import { useAuthState } from 'react-firebase-hooks/auth';
import { auth } from '../firebaseConfig';
import { signOut } from 'firebase/auth';
import ReactDOM from 'react-dom';

const NavRail = () => {
  const [loginOpen, setLoginOpen] = useState(false);
  const [currentUser, loading] = useAuthState(auth);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [displayUser, setDisplayUser] = useState(null);

  useEffect(() => {
    if (!loading && !isSigningOut) {
      setDisplayUser(currentUser);
      if (currentUser) setLoginOpen(false);
    }
  }, [loading, currentUser, isSigningOut]);

  const handleLoginClick = (e) => {
    e.preventDefault(); // Prevent navigation
    setLoginOpen(true);
  };

  const handleSignOut = async () => {
    const userBeforeSignOut = currentUser;
    ReactDOM.flushSync(() => {
      setIsSigningOut(true);
      setDisplayUser(userBeforeSignOut);
    });
    
    const startTime = Date.now();
    
    try {
      await signOut(auth);
    } finally {
      const elapsed = Date.now() - startTime;
      const remainingDelay = Math.max(1000 - elapsed, 0);
      await new Promise(resolve => setTimeout(resolve, remainingDelay));
      
      ReactDOM.flushSync(() => {
        setIsSigningOut(false);
        setLoginOpen(false);
        setDisplayUser(null);
      });
    }
  };

  return (
    <Box
      sx={{
        width: 240,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f3f4f6',
        p: 2,
        boxShadow: 3,
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 100
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

        {loading ? (
          <ListItem>
            <Typography variant="body2">Loading...</Typography>
          </ListItem>
        ) : !displayUser ? (
          <ListItem disablePadding>
            <ListItemButton
              onClick={handleLoginClick}
              sx={{
                '&:hover': { backgroundColor: '#e0e0e0' },
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
        ) : (
          <>
            <ListItem disablePadding component="div">
              <ListItemIcon sx={{ minWidth: '40px' }}>
                <AccountCircleIcon />
              </ListItemIcon>
              <ListItemText 
                primary={displayUser?.email?.split('@')[0] || ''} 
                secondary={displayUser?.email || ''} 
              />
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                onClick={handleSignOut}
                disabled={isSigningOut}
                sx={{
                  '&:hover': { backgroundColor: '#e0e0e0' },
                  gap: 1,
                  borderRadius: 1,
                  px: 2,
                }}
              >
                <ListItemIcon sx={{ minWidth: '40px' }}>
                  {isSigningOut ? <CircularProgress size={24} /> : <LogoutIcon />}
                </ListItemIcon>
                <ListItemText primary={isSigningOut ? "Signing out..." : "Sign Out"} />
              </ListItemButton>
            </ListItem>
          </>
        )}
      </List>

      <LoginModal 
        open={loginOpen} 
        onClose={() => setLoginOpen(false)} 
      />
    </Box>
  );
};

export default NavRail;
