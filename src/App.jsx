import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import theme from './theme';
import Layout from './Layout';
import Home from './pages/Home';
import JobHistory from './pages/JobHistory';
import AlgoForm from './components/AlgoForm';
import AlgorithmsPage from './pages/Algorithms';

function App() {
  return (
    <Router>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/algorithms" element={<AlgorithmsPage />} />
            <Route path="/history" element={<JobHistory />} />
          </Routes>
        </Layout>
      </ThemeProvider>
    </Router>
  );
}

export default App;