import { getFirestore, collection, addDoc } from 'firebase/firestore'; 
import { app } from './firebaseConfig';  // Your firebase config

const db = getFirestore(app);

export const addUser = async (userData) => {
  try {
    await addDoc(collection(db, 'users'), userData);
  } catch (e) {
    console.error("Error adding document: ", e);
  }
};