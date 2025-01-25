import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { motion } from 'framer-motion';
import Layout from './Layout';
import Home from './pages/Home';
import Algorithms from './pages/Algorithms';
import History from './pages/History';

// Define the light theme
const lightTheme = createTheme({
  palette: {
    mode: 'light',
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <BrowserRouter>
        <AnimatePresence mode='wait'>
          <Routes>
            <Route element={<Layout />}>
              <Route
                path="/"
                element={
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    <Home />
                  </motion.div>
                }
              />
              <Route
                path="/algorithms"
                element={
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    <Algorithms />
                  </motion.div>
                }
              />
              <Route
                path="/history"
                element={
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    <History />
                  </motion.div>
                }
              />
              {/* Add other routes here */}
            </Route>
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);