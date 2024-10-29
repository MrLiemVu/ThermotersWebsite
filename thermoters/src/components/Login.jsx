import React, { useState } from 'react';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc } from 'firebase/firestore';
import app from '../../firebaseConfig';
import { Button, Typography, Alert, Box } from '@mui/material';

// Initialize Firebase Auth, Firestore, and Google Provider
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

export const signInWithGoogle = async () => {
  try {
    // Sign in with Google
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // Reference to the user's Firestore document
    const userRef = doc(db, "users", user.uid);
    const userSnap = await getDoc(userRef);

    // Check if user document exists
    if (!userSnap.exists()) {
      // Add new user to Firestore if they are a new user
      await setDoc(userRef, {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        createdAt: new Date(),
      });
      console.log("New user added to Firestore");
    } else {
      console.log("User already exists in Firestore");
    }

    return user;
  } catch (error) {
    console.error("Google Sign-In Error:", error);
    throw error; // Throwing error to handle it in the component
  }
};

function Login() {
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null); // State to hold the authenticated user

  const handleGoogleSignIn = async () => {
    try {
      setError(null);
      const signedInUser = await signInWithGoogle();
      console.log("User signed in successfully:", signedInUser);
      
      // Set the user state to the signed-in user
      setUser(signedInUser);

      // Redirect or perform additional actions as needed, e.g., navigating to a dashboard
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      mt={5}
      p={3}
      boxShadow={3}
      borderRadius={2}
      width={300}
      mx="auto"
    >
      <Typography variant="h5" gutterBottom>
        Sign in with Google
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Button
        variant="contained"
        color="primary"
        onClick={handleGoogleSignIn}
        fullWidth
      >
        Login with Google
      </Button>

      {/* Display user information if signed in */}
      {user && (
        <Typography variant="body1" sx={{ mt: 2 }}>
          Welcome, {user.displayName}!
        </Typography>
      )}
    </Box>
  );
}

export default Login;