import React, { useState } from 'react';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore';
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

    // Reference to the user document
    const userRef = doc(db, "users", user.uid);
    const userSnap = await getDoc(userRef);

    if (!userSnap.exists()) {
      // Create new user document with basic info
      await setDoc(userRef, {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        createdAt: serverTimestamp(),
        lastLogin: serverTimestamp(),
      }, { merge: true }); // Use merge to avoid overwriting existing data
      console.log("New user added to Firestore");
    } else {
      // Update last login for existing users
      await setDoc(userRef, {
        lastLogin: serverTimestamp()
      }, { merge: true });
      console.log("User login updated in Firestore");
    }

    return user;
  } catch (error) {
    console.error("Error during sign in:", error);
    throw error;
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