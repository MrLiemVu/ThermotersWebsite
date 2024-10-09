# ThermotersWebsite

init firebase
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBZuDIOXoVfH6Tk1HQBuI35p42q3YXy8B0",
  authDomain: "thermoters.firebaseapp.com",
  projectId: "thermoters",
  storageBucket: "thermoters.appspot.com",
  messagingSenderId: "578904774460",
  appId: "1:578904774460:web:e80cd1f4df7f3c36c53039",
  measurementId: "G-45MEYP86M9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);