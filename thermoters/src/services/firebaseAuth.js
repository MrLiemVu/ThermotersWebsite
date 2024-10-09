import { getAuth } from 'firebase/auth';
import { app } from './firebaseConfig';  // Your firebase config

const auth = getAuth(app);

export const signInWithEmail = (email, password) => {
  return auth.signInWithEmailAndPassword(email, password);
};

export const signOut = () => {
  return auth.signOut();
};