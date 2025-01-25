module.exports = {
    presets: [
      ['@babel/preset-env', { modules: 'auto' }],
      '@babel/preset-react'
    ],
    plugins: [
      ['babel-plugin-transform-import-meta', {
        module: 'ES6',
        env: {
          VITE_FIREBASE_API_KEY: process.env.VITE_FIREBASE_API_KEY,
          VITE_FIREBASE_AUTH_DOMAIN: process.env.VITE_FIREBASE_AUTH_DOMAIN,
          VITE_FIREBASE_PROJECT_ID: process.env.VITE_FIREBASE_PROJECT_ID,
          VITE_FIREBASE_STORAGE_BUCKET: process.env.VITE_FIREBASE_STORAGE_BUCKET,
          VITE_FIREBASE_MESSAGING_SENDER_ID: process.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
          VITE_FIREBASE_APP_ID: process.env.VITE_FIREBASE_APP_ID
        }
      }],
      '@babel/plugin-transform-modules-commonjs',
      '@babel/plugin-transform-runtime'
    ]
  };