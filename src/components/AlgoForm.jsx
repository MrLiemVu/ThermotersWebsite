// src/components/AlgoForm.js
import React, { useState } from 'react';
import {
  TextField,
  Button,
  Box,
  FormControl,
  FormControlLabel,
  Checkbox,
  Paper,
  Typography,
  Alert,
  Fade,
  CircularProgress,
} from '@mui/material';
import { addDoc, collection, serverTimestamp } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { db } from '../../firebaseConfig';

const AlgoForm = () => {
  const [formData, setFormData] = useState({
    jobTitle: '',
    sequence: '',
    file: null,
    extended: false,
    reverseComplement: false,
    maxValue: -2.5,
    minValue: -6,
    isPrefix: false,
    isSuffix: false,
    predictors: {
      standard: false,
      standardSpacer: false,
      standardSpacerCumulative: false,
    },
    pointsToOne: false,
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDescription, setShowDescription] = useState(true);
  const auth = getAuth();

  // Handle input change for text fields
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle checkbox change
  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: checked
    }));
  };

  // Handle file upload
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setFormData(prev => ({
      ...prev,
      file: file
    }));
  };

  // Handle predictor change
  const handlePredictorChange = (e) => {
    const { name, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      predictors: {
        ...prev.predictors,
        [name]: checked
      }
    }));
  };

  // Handle sequence validation
  const handleValidSequence = (input) => {
    // Remove any non-ACTGU characters (case insensitive)
    const cleaned = input.toUpperCase().replace(/[^ACGTU]/gi, '');
    setFormData(prev => ({
      ...prev,
      sequence: cleaned
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setIsSubmitting(true);
    setShowDescription(false);

    const startTime = Date.now();

    if (!auth.currentUser) {
      setError('Please login to submit a job');
      setIsSubmitting(false);
      setShowDescription(true);
      return;
    }

    if (!formData.jobTitle) {
      setError('Please enter a job title');
      setIsSubmitting(false);
      setShowDescription(true);
      return;
    }

    if (!formData.sequence && !formData.file) {
      setError('Please enter a sequence or upload a file');
      setIsSubmitting(false);
      setShowDescription(true);
      return;
    }

    try {
      // Prepare the job data
      const jobData = {
        userId: auth.currentUser.uid,
        jobTitle: formData.jobTitle,
        sequence: formData.sequence,
        fileName: formData.file?.name || null,
        fileContent: null, // Will be handled by Cloud Function
        extended: formData.extended,
        reverseComplement: formData.reverseComplement,
        maxValue: formData.maxValue,
        minValue: formData.minValue,
        isPrefix: formData.isPrefix,
        isSuffix: formData.isSuffix,
        predictors: formData.predictors,
        pointsToOne: formData.pointsToOne,
        status: 'pending',
        createdAt: serverTimestamp(),
      };

      // OPTION 1: Save to user-specific collection
      // Path: /users/{userId}/jobs/{jobId}
      const userJobsRef = collection(db, "users", auth.currentUser.uid, "jobs");
      const docRef = await addDoc(userJobsRef, jobData);

      // OPTION 2: Save to general jobs collection with user ID field
      // Path: /jobs/{jobId}
      // const jobsRef = collection(db, "jobs");
      // const docRef = await addDoc(jobsRef, jobData);

      // If there's a file, handle it separately
      if (formData.file) {
        // TODO: Upload file to Firebase Storage
        // This could be handled here or in the Cloud Function
      }

      setSuccess(true);
      // Reset form
      setFormData({
        jobTitle: '',
        sequence: '',
        file: null,
        extended: false,
        reverseComplement: false,
        maxValue: -2.5,
        minValue: -6,
        isPrefix: false,
        isSuffix: false,
        predictors: {
          standard: false,
          standardSpacer: false,
          standardSpacerCumulative: false,
        },
        pointsToOne: false,
      });
    } catch (error) {
      console.error('Error submitting job:', error);
      setError('Error submitting job. Please try again.');
    } finally {
      const elapsed = Date.now() - startTime;
      const remainingDelay = Math.max(1000 - elapsed, 0);
      await new Promise(resolve => setTimeout(resolve, remainingDelay));
      
      setIsSubmitting(false);
      setShowDescription(true);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Job submitted successfully!
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Submit New Job
        </Typography>

        {/* Job Title */}
        <TextField
          label="Job Title"
          name="jobTitle"
          value={formData.jobTitle}
          onChange={handleChange}
          fullWidth
          required
          sx={{ mb: 3 }}
        />

        {/* Sequence Input */}
        <TextField
          label="Sequence"
          name="sequence"
          value={formData.sequence}
          onChange={(e) => handleValidSequence(e.target.value)}
          multiline
          rows={4}
          fullWidth
          sx={{ mb: 3 }}
          inputProps={{ 
            maxLength: 1000,
            pattern: '[ACGTacgt]*', // HTML5 validation
            title: 'Only A, C, G, T/U characters allowed' 
          }}
        />

        {/* File Upload */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Or Upload File:
          </Typography>
          <Button
            variant="outlined"
            component="label"
            sx={{ 
              borderRadius: 2,
              textTransform: 'none'
            }}
          >
            Choose File
            <input
              type="file"
              hidden
              accept=".csv,.fna,.ffn,.faa"
              onChange={handleFileUpload}
            />
          </Button>
          {formData.file && (
            <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
              Selected file: {formData.file.name}
            </Typography>
          )}
        </Box>

        {/* Predictor Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Select Predictors:
          </Typography>
          <FormControl component="fieldset">
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.predictors.standard}
                  onChange={handlePredictorChange}
                  name="standard"
                />
              }
              label="Standard"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.predictors.standardSpacer}
                  onChange={handlePredictorChange}
                  name="standardSpacer"
                />
              }
              label="Standard + Spacer"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.predictors.standardSpacerCumulative}
                  onChange={handlePredictorChange}
                  name="standardSpacerCumulative"
                />
              }
              label="Standard + Spacer + Cumulative"
            />
        {/* Extended Model Checkbox */}
        <FormControlLabel
          control={
            <Checkbox
              checked={formData.extended}
              onChange={handleCheckboxChange}
              name="extended"
            />
          }
          label="Use Extended Model (Recommended)"
        />
      </FormControl>
    </Box>
    <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Sequence Parameters:
          </Typography>            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.reverseComplement}
                  onChange={handleCheckboxChange}
                  name="reverseComplement"
                />
              }
              label="Reverse Complement"
            />
            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.pointsToOne}
                    onChange={handleCheckboxChange}
                    name="pointsToOne"
                  />
                }
                label="Points to +1"
              />
            </Box>
            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.isPrefix}
                    onChange={handleCheckboxChange}
                    name="isPrefix"
                  />
                }
                label="Add Prefix + Suffix Gs"
              />
            </Box>
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <TextField
                label="Maximum Value"
                type="number"
                name="maxValue"
                value={formData.maxValue}
                onChange={handleChange}
                inputProps={{ step: 0.1 }}
                sx={{ width: '150px' }}
              />
              <TextField
                label="Minimum Value"
                type="number"
                name="minValue"
                value={formData.minValue}
                onChange={handleChange}
                inputProps={{ step: 0.1 }}
                sx={{ width: '150px' }}
              />
            </Box>
          </Box>
      </Paper>

      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        size="large"
        sx={{ mb: 3 }}
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <>
            <CircularProgress size={24} sx={{ mr: 1 }} />
            Submitting...
          </>
        ) : (
          "Submit Job"
        )}
      </Button>

      {/* Description Section */}
      <Fade in={showDescription} timeout={1000}>
        <Paper sx={{ p: 3, mt: 3, backgroundColor: '#f3e5f5'  }}>
          <Typography variant="subtitle2" gutterBottom>
            Supported File Types:
          </Typography>
          <Box component="div" sx={{ pl: 2 }}>
            <Typography variant="body2" component="div">
              <ul>
                <li>Excel spreadsheet (.csv)</li>
                <li>FASTA nucleic acid (.fna)</li>
                <li>FASTA nucleotide of gene regions (.ffn)</li>
                <li>FASTA amino acid (.faa)</li>
              </ul>
            </Typography>
          </Box>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Predictor Types:
          </Typography>
          <Box component="div" sx={{ pl: 2 }}>
            <Typography variant="body2" component="div">
              <ul>
                <li>Standard: estimates expression level only from a single sigma70 binding site with the lowest binding energy.</li>
                <li>Standard + Spacer: accounts for energy penalties with different spacer configurations.</li>
                <li>Standard + Spacer + Cumulative: accounts for all possible sigma70 binding sites with energy associated with different spacer configurations.</li>
              </ul>
            </Typography>
          </Box>
          <Typography variant="h6" gutterBottom>
            How To Use
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Step 1:</strong> Enter your sequence directly in the text field or upload a file in one of the supported formats.
            </Typography>
            <Typography variant="body2" paragraph>
            <strong>Step 2:</strong> Choose your preferred prediction algorithm from the available options.
            </Typography>
            <Typography variant="body2" paragraph>
            <strong>Step 3:</strong> Select your strand direction:
            • Forward strand (input sequence from left to right)
            • Reverse complement
            • Both directions          
            </Typography>
            <Typography variant="body2" paragraph>
            <strong>Important Note:</strong> The first upstream 35 base pairs in the sequence cannot be evaluated (due to the minimum 
            binding site length of sigma70). Please include at least 35bp upstream of your sequence of interest. These can be 
            a string of Gs to help with interpretation.
            </Typography>

            <div>
              <Typography variant="body2" paragraph>
                <strong>Output:</strong> Results will include:
              </Typography>
              <ul>
                <li>Brick plot visualization</li>
                <li>Predicted expression level (Pon)</li>
              </ul>
            </div>
            <Typography variant="body2" paragraph>
            <strong>Sequence Limit:</strong> Registered users can input up to 100 sequences per 6 months.
          </Typography>
        </Paper>
      </Fade>
    </Box>
  );
};

export default AlgoForm;