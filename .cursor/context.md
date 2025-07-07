# Thermoters Gene Expression Prediction Platform - Context for AI Assistant

## Project Overview

Thermoters is a React-based web application for predicting bacterial sigma70 binding sites and constitutive expression levels from DNA sequences. The platform provides an intuitive interface for users to submit DNA sequences and receive predictions through a sophisticated algorithm pipeline.

## Key Features

1. **Sequence Analysis**: Submit DNA sequences for sigma70 binding site analysis
2. **Brick Plot Generation**: Visual representation of binding energies across sequences
3. **Expression Prediction**: Multiple algorithms for predicting constitutive expression levels
4. **User Authentication**: Firebase-based user management with usage tracking
5. **Job History**: Track and review previous analysis jobs
6. **Real-time Processing**: Cloud Functions for backend processing

## Architecture

### Frontend Stack

- **React 18+**: Modern React with hooks and functional components
- **Material-UI**: Component library for consistent UI design
- **React Router**: Client-side routing and navigation
- **Firebase**: Authentication, Firestore database, and Cloud Functions
- **Vite**: Fast build tool and development server
- **Jest**: Testing framework with React Testing Library

### Backend Services

- **Firebase Cloud Functions**: Serverless backend processing
- **Python Processing**: Scientific computing for sequence analysis
- **Firestore**: Real-time database for job tracking and user data

### Technology Stack

- **JavaScript/ES6+**: Modern JavaScript features
- **Material-UI**: UI component library
- **Firebase**: Backend-as-a-Service
- **React Router**: Navigation
- **Jest**: Testing framework
- **ESLint**: Code linting and formatting

## Development Standards

### Code Quality

- **TypeScript**: Use TypeScript for new components and functions
- **ESLint**: Zero linting errors in main branch
- **Testing**: ≥80% code coverage with Jest and React Testing Library
- **Modern React**: Use functional components with hooks
- **Material-UI**: Consistent component usage and theming

### React Best Practices

- **Functional Components**: Use hooks instead of class components
- **State Management**: Use useState, useReducer, and Context appropriately
- **Performance**: Use React.memo() for expensive components
- **Error Boundaries**: Implement proper error handling
- **Accessibility**: Follow WCAG guidelines

### Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── AlgoForm.jsx    # Main sequence submission form
│   ├── HistoryTable.jsx # Job history display
│   ├── LoginModal.jsx  # Authentication modal
│   ├── Login.jsx       # Login component
│   └── NavRail.jsx     # Navigation component
├── pages/              # Page components
│   ├── Home.jsx        # Landing page with explanation
│   ├── Algorithms.jsx  # Algorithm selection page
│   └── History.jsx     # Job history page
├── services/           # API and service functions
│   ├── firebaseAuth.js # Firebase authentication
│   └── firestore.js    # Firestore database operations
├── styles/             # CSS and styling
├── assets/             # Static assets and images
└── theme.js            # Material-UI theme configuration
```

## Common Patterns

### Component Implementation

```jsx
import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';

const ExampleComponent = ({ title, data }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Component initialization logic
    return () => {
      // Cleanup logic
    };
  }, []);

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    
    try {
      // API call logic
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {/* Component content */}
    </Paper>
  );
};

export default ExampleComponent;
```

### Firebase Integration Pattern

```jsx
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';

const useFirebaseAuth = () => {
  const auth = getAuth();
  
  const login = async (email, password) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    } catch (error) {
      throw new Error(`Login failed: ${error.message}`);
    }
  };

  const getUserData = async (userId) => {
    const userDoc = doc(db, 'users', userId);
    const userSnap = await getDoc(userDoc);
    return userSnap.exists() ? userSnap.data() : null;
  };

  return { login, getUserData };
};
```

### Form Handling Pattern

```jsx
import React, { useState } from 'react';
import { TextField, Button, Box } from '@mui/material';

const FormComponent = () => {
  const [formData, setFormData] = useState({
    sequence: '',
    jobTitle: '',
    extended: false
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.sequence.trim()) {
      newErrors.sequence = 'Sequence is required';
    }
    if (!formData.jobTitle.trim()) {
      newErrors.jobTitle = 'Job title is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    // Submit logic here
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        name="sequence"
        value={formData.sequence}
        onChange={handleChange}
        error={!!errors.sequence}
        helperText={errors.sequence}
        fullWidth
        multiline
        rows={4}
        label="DNA Sequence"
      />
      {/* Other form fields */}
    </Box>
  );
};
```

## Testing Patterns

### Component Testing

```jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AlgoForm from '../components/AlgoForm';

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('AlgoForm', () => {
  test('submits form with valid data', async () => {
    renderWithRouter(<AlgoForm />);
    
    const sequenceInput = screen.getByLabelText(/sequence/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });
    
    fireEvent.change(sequenceInput, {
      target: { value: 'ATCGATCG' }
    });
    
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/submitted/i)).toBeInTheDocument();
    });
  });
});
```

## Firebase Integration

### Authentication

```jsx
import { useAuthState } from 'react-firebase-hooks/auth';
import { getAuth } from 'firebase/auth';

const useAuth = () => {
  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);
  
  return {
    user,
    loading,
    error,
    isAuthenticated: !!user
  };
};
```

### Firestore Operations

```jsx
import { collection, addDoc, query, where, orderBy } from 'firebase/firestore';
import { db } from '../firebaseConfig';

const submitJob = async (jobData) => {
  try {
    const docRef = await addDoc(collection(db, 'jobs'), {
      ...jobData,
      createdAt: serverTimestamp(),
      status: 'pending'
    });
    return docRef.id;
  } catch (error) {
    throw new Error(`Failed to submit job: ${error.message}`);
  }
};

const getUserJobs = (userId) => {
  const jobsRef = collection(db, 'jobs');
  return query(
    jobsRef,
    where('userId', '==', userId),
    orderBy('createdAt', 'desc')
  );
};
```

## Error Handling

### Common Patterns

```jsx
const handleApiCall = async () => {
  try {
    setLoading(true);
    setError(null);
    
    const result = await apiFunction();
    setData(result);
  } catch (error) {
    console.error('API call failed:', error);
    setError(error.message || 'An unexpected error occurred');
  } finally {
    setLoading(false);
  }
};
```

## Performance Considerations

### Optimization

- Use React.memo() for expensive components
- Implement proper loading states
- Optimize bundle size with code splitting
- Use proper image optimization
- Implement virtual scrolling for large lists

### Memory Management

- Clean up event listeners in useEffect
- Cancel API requests on component unmount
- Clear intervals and timeouts
- Use proper dependency arrays in useEffect

## Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Implement proper authentication checks
- Use Firebase security rules

## Current Integrations

- Firebase Authentication and Firestore
- Material-UI for consistent UI
- React Router for navigation
- Jest for testing
- ESLint for code quality
- Vite for build tooling

## Algorithm Details

### Sigma70 Binding Analysis

The platform implements statistical thermodynamics models to:

1. **Identify Binding Sites**: Analyze DNA sequences for sigma70 binding affinity
2. **Generate Brick Plots**: Visual representation of binding energies
3. **Predict Expression**: Convert binding energies to expression level predictions

### Available Models

- **Standard Model**: Single binding site analysis
- **Standard + Spacer**: Accounts for spacer configuration penalties
- **Extended Model**: Comprehensive analysis of all possible binding sites

This context should help you understand the project structure, coding standards, and common patterns used throughout the Thermoters gene expression prediction platform.
