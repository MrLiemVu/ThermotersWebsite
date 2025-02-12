const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Core Functions
exports.createUserDocument = functions.auth.user().onCreate(handleUserCreation);
exports.processJob = functions.firestore.document('users/{userId}/jobs/{jobId}').onCreate(handleJobProcessing);

// Shared Constants
const JOB_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  ERROR: 'error'
};

async function handleUserCreation(user) {
  try {
    const sanitizedEmail = user.email
      .replace(/@/g, '_at_')
      .replace(/\./g, '_dot_')
      .replace(/[^a-zA-Z0-9_-]/g, '');

    const docId = `${sanitizedEmail}-${user.uid}`;
    const userDocRef = admin.firestore().collection('users').doc(docId);

    await userDocRef.set({
      uid: user.uid,
      email: user.email,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      lastLogin: admin.firestore.FieldValue.serverTimestamp(),
      lastJob: null
    });

    console.log(`Created user document: ${docId}`);
  } catch (error) {
    console.error('Error creating user document:', error);
    throw new functions.https.HttpsError('internal', 'User document creation failed');
  }
}

async function handleJobProcessing(snap, context) {
  const jobData = snap.data();
  const jobId = context.params.jobId;
  const userId = context.params.userId;

  try {
    // Update job status to processing
    await snap.ref.update({
      status: JOB_STATUS.PROCESSING,
      processingStartedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // TODO: Implement your actual processing logic here
    const processedData = await processGeneData(jobData);
    
    // Update job with results
    await snap.ref.update({
      status: JOB_STATUS.COMPLETED,
      results: processedData,
      completedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Update user's last job reference
    const userDocRef = admin.firestore().collection('users').doc(userId);
    await userDocRef.update({
      lastJob: jobId
    });

  } catch (error) {
    console.error('Error processing job:', error);
    await snap.ref.update({
      status: JOB_STATUS.ERROR,
      error: error.message,
      errorAt: admin.firestore.FieldValue.serverTimestamp()
    });
  }
}

// TODO: Implement your actual processing logic
async function processGeneData(jobData) {
  return {
    brickplot: "Sample brickplot data",
    predictors: jobData.predictors,
    sequence: jobData.sequence
  };
}

// Option 2: Trigger on general jobs collection
// exports.processJob = functions.firestore
//     .document('jobs/{jobId}')
//     .onCreate((snap, context) => {
//         // Similar logic as above
//     }); 