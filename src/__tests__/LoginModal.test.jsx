import React from 'react';
import { render, screen } from '@testing-library/react';
import LoginModal from '../components/LoginModal';

describe('LoginModal', () => {
  it('renders without crashing', () => {
    render(<LoginModal open={true} onClose={() => {}} />);
    expect(screen.getByText('Login with Google')).toBeInTheDocument();
  });
});