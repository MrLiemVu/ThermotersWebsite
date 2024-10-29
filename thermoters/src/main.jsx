import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';

// Define the light theme
const lightTheme = createTheme({
  palette: {
    mode: 'light',
  },
});

const root = createRoot(document.getElementById('root'));
root.render(
  <StrictMode>
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>
);