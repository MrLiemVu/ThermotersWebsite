const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Option 1: Trigger on user-specific collection
exports.processJob = functions.firestore
    .document('users/{userId}/jobs/{jobId}')
    .onCreate(async (snap, context) => {
        const jobData = snap.data();
        const jobId = context.params.jobId;
        const userId = context.params.userId;

        try {
            // Update the job status to processing
            await snap.ref.update({
                status: 'processing',
                processingStartedAt: admin.firestore.FieldValue.serverTimestamp()
            });

            // TODO: Your job processing logic here
            // 1. Run your gene expression prediction algorithm
            // 2. Generate results
            // 3. Store results

            // Update the job with results
            await snap.ref.update({
                status: 'completed',
                results: 'Your results here',
                completedAt: admin.firestore.FieldValue.serverTimestamp()
            });

        } catch (error) {
            console.error('Error processing job:', error);
            await snap.ref.update({
                status: 'error',
                error: error.message,
                errorAt: admin.firestore.FieldValue.serverTimestamp()
            });
        }
    });

// Option 2: Trigger on general jobs collection
// exports.processJob = functions.firestore
//     .document('jobs/{jobId}')
//     .onCreate((snap, context) => {
//         // Similar logic as above
//     }); 