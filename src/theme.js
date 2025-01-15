import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: [
      '-apple-system',
      'Segoe UI',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    // Main title
    h3: {
      fontFamily: 'Segoe UI',
      fontWeight: 700,
    },
    // Subtitle
    h5: {
      fontFamily: 'Segoe UI',
      fontWeight: 400,
    },
    // Regular text
    body1: {
      fontFamily: 'Segoe UI',
      fontSize: '1rem',
    },
    // Smaller text
    body2: {
      fontFamily: 'Segoe UI',
      fontSize: '0.875rem',
    },
    // Add this to ensure all variants use Segoe UI
    allVariants: {
      fontFamily: 'Segoe UI',
    },
  },
  components: {
    // This ensures MUI components also use the font
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          fontFamily: 'Segoe UI',
        },
      },
    },
  },
});

export default theme; 