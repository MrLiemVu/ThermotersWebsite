import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  Box, 
  Typography, 
  Button, 
  Alert,
  Backdrop,
  CircularProgress
} from '@mui/material';
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from '../../firebaseConfig'; // Add this import if needed
import { useAuthState } from 'react-firebase-hooks/auth';
import GoogleIcon from '@mui/icons-material/Google';

const LoginModal = ({ open, onClose }) => {
  const [error, setError] = useState(null);
  const [user] = useAuthState(auth);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      setIsLoading(false); // Reset loading state when user logs out
    }
  }, [user]);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      await signInWithPopup(auth, new GoogleAuthProvider());
    } finally {
      setIsLoading(false);
      onClose();
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      closeAfterTransition
      slots={{ backdrop: Backdrop }}
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(3px)'
          }
        }
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          borderRadius: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          alignItems: 'center'
        }}
      >
        <Typography variant="h5" component="h2">
          Sign in with Google
        </Typography>

        {error && (
          <Alert severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        )}

        <Button
          variant="contained"
          onClick={handleGoogleLogin}
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : <GoogleIcon />}
          fullWidth
          sx={{ mt: 2 }}
        >
          {isLoading ? 'Signing in...' : 'Login with Google'}
        </Button>

        {user && (
          <Typography variant="body1">
            Welcome, {user.displayName}!
          </Typography>
        )}
      </Box>
    </Modal>
  );
};

export default LoginModal; 