export const auth = {
  currentUser: { uid: 'test-user' },
  signInWithPopup: jest.fn(),
};

export const db = {
  collection: jest.fn(),
  doc: jest.fn(),
  addDoc: jest.fn(),
};

export const storage = {
  ref: jest.fn(),
  uploadBytes: jest.fn(),
};