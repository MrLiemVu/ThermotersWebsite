module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.cjs'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  transformIgnorePatterns: [
    '/node_modules/(?!(firebase|@firebase|@mui)/)'
  ],
  setupFiles: ['<rootDir>/jest.setup.cjs'],
  globals: {
    // This is now handled by dotenv in jest.setup.cjs
  }
}; 