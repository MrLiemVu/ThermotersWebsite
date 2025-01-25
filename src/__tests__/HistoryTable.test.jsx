import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import HistoryTable from '../components/HistoryTable';
import { getDocs } from 'firebase/firestore';

// Mock firestore response
jest.mock('firebase/app', () => ({
  initializeApp: jest.fn(),
}));

jest.mock('firebase/firestore', () => ({
  getFirestore: jest.fn(),
  getDocs: jest.fn(() => ({
    docs: [{
      id: '1',
      data: () => ({
        jobName: 'Test Job',
        status: 'completed',
        uploadedAt: { seconds: Date.now()/1000 }
      })
    }]
  }))
}));

describe('HistoryTable', () => {
  it('should display job history', async () => {
    render(<HistoryTable />);
    
    // Wait for data to load
    const jobName = await screen.findByText('Test Job');
    const status = await screen.findByText('completed');
    
    expect(jobName).toBeInTheDocument();
    expect(status).toBeInTheDocument();
  });
});