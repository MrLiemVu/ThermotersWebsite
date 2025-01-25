import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlgoForm from '../components/AlgoForm';

// Mock firestore
jest.mock('firebase/app', () => ({
  initializeApp: jest.fn(),
}));

jest.mock('firebase/firestore', () => ({
  getFirestore: jest.fn(),
  collection: jest.fn(),
  addDoc: jest.fn(),
  serverTimestamp: jest.fn(),
}));

jest.mock('firebase/auth', () => ({
  getAuth: jest.fn(),
}));

describe('AlgoForm', () => {
  it('should submit form with valid data', async () => {
    render(<AlgoForm />);
    
    // Use more reliable queries
    const jobTitleInput = screen.getByRole('textbox', { name: /job title/i });
    const sequenceInput = screen.getByRole('textbox', { name: /sequence/i });
    const extendedCheckbox = screen.getByLabelText(/use extended model/i);
    
    // Simulate user input
    await userEvent.type(jobTitleInput, 'Test Job');
    await userEvent.type(sequenceInput, 'ATCG');
    await userEvent.click(extendedCheckbox);
    
    // Submit form
    await userEvent.click(screen.getByRole('button', { name: /submit job/i }));

    // Verify submission
    expect(addDoc).toHaveBeenCalledWith(
      expect.any(Object), // collection reference
      expect.objectContaining({
        jobTitle: 'Test Job',
        sequence: 'ATCG',
        extended: true
      })
    );
  });
});