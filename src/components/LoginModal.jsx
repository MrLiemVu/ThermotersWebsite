import React, { useState } from 'react';
import { 
  Modal, 
  Box, 
  Typography, 
  Button, 
  Alert,
  Backdrop
} from '@mui/material';
import { signInWithGoogle } from './Login'; // Reusing the existing login logic

const LoginModal = ({ open, onClose }) => {
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  const handleGoogleSignIn = async () => {
    try {
      setError(null);
      const signedInUser = await signInWithGoogle();
      setUser(signedInUser);
      onClose(); // Close modal after successful login
    } catch (error) {
      setError(error.message);
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