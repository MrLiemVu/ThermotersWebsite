import React, { useState } from 'react';
import { 
  Modal, 
  Box, 
  Typography, 
  Button, 
  Alert,
  Backdrop
} from '@mui/material';
import { signInWithGoogle } from './Login';
import { auth } from '../../firebaseConfig'; // Add this import if needed

const LoginModal = ({ open, onClose }) => {
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [disabled, setDisabled] = useState(false);

  const handleGoogleSignIn = async () => {
    try {
      setError(null);
      setDisabled(true);
      const signedInUser = await signInWithGoogle();
      
      // Wait for Firestore write to complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setUser(signedInUser);
      onClose();
      
      // Force refresh to ensure authentication state is updated
      window.location.reload();
    } catch (error) {
      if (error.code !== 'auth/cancelled-popup-request') {
        setError(error.message);
      }
    } finally {
      setDisabled(false);
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
          color="primary"
          onClick={handleGoogleSignIn}
          fullWidth
          sx={{ mt: 2 }}
          disabled={disabled}
        >
          Login with Google
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