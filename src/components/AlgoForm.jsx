// src/components/AlgoForm.js
import React, { useState, useEffect } from 'react';
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
import { addDoc, collection, serverTimestamp, doc, onSnapshot } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { db } from '../../firebaseConfig';
import { httpsCallable } from 'firebase/functions';
import { functions } from '../../firebaseConfig';

const AlgoForm = () => {
  const [formData, setFormData] = useState({
    jobTitle: '',
    sequence: '',
    file: null,
    extended: false,
    reverseComplement: false,
    maxValue: -2.5,
    minValue: -6,
    threshold: -2.5,
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
  const [results, setResults] = useState({
    image: null,
    analysis: null,
    loading: false
  });
  const [usageCount, setUsageCount] = useState(0);
  const auth = getAuth();

  useEffect(() => {
    if (auth.currentUser) {
      const userRef = doc(db, "users", auth.currentUser.uid);
      onSnapshot(userRef, (doc) => {
        if (doc.exists()) {
          setUsageCount(doc.data().monthlyUsage?.count || 0);
        }
      });
    }
  }, [auth.currentUser]);

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
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFormData(prev => ({
          ...prev,
          file: file,
          fileContent: e.target.result,  // Store file content
          fileName: file.name
        }));
      };
      reader.readAsText(file);
    }
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
      // First hit the ping endpoint
      const pingResponse = await fetch(
        `https://us-central1-${import.meta.env.VITE_FIREBASE_PROJECT_ID}.cloudfunctions.net/ping`
      );
      
      if (!pingResponse.ok) {
        throw new Error('Failed to connect to server');
      }
      
      const pingData = await pingResponse.json();
      console.log('Ping successful:', pingData);

      // Then submit the job as normal
      const submitJob = httpsCallable(functions, 'submit_job');
      const result = await submitJob({
        jobTitle: formData.jobTitle,
        sequence: formData.sequence,
        fileContent: formData.fileContent,
        fileName: formData.fileName,
        predictors: formData.predictors,
        model: 'default',
        isPlusOne: formData.pointsToOne,
        isRc: formData.reverseComplement,
        maxValue: formData.maxValue,
        minValue: formData.minValue,
        threshold: -2.5,
        isPrefixSuffix: formData.isPrefix
      });
      
      const data = await result.data;
      
      if (data.image && data.analysis) {
        setResults({
          image: data.image,
          analysis: data.analysis,
          loading: false
        });
      }
      
      console.log('Job submitted:', data.jobId);
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

      // When saving jobs
      const docRef = db.collection('users').doc(auth.currentUser.uid)
                    .collection('jobs').doc(data.jobId);  // Must match Firestore path
    } catch (error) {
      console.error('Submission error:', error);
      setError(error.message);
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
              accept=".csv,.fna,.ffn,.faa,.fasta"
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
              <TextField
                label="Threshold"
                type="number"
                name="threshold"
                value={formData.threshold}
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
        disabled={isSubmitting || results.loading}
      >
        {results.loading ? (
          <>
            <CircularProgress size={24} sx={{ mr: 1 }} />
            Processing...
          </>
        ) : isSubmitting ? (
          "Submitting..."
        ) : (
          "Submit Job"
        )}
      </Button>

      {/* Error/Success Messages */}
      <Box sx={{ mb: 3 }}>
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
        {auth.currentUser && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Sequences used this month: {usageCount}/100
          </Alert>
        )}
      </Box>

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
                <li>FASTA (.fasta)</li>
              </ul>
            </Typography>
          </Box>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Predictor Types:
          </Typography>
          <Box component="div" sx={{ pl: 2 }}>
            <Typography variant="body2" component="div">
              <ul>
                <li><strong>Standard</strong>: Predicts expression based on the strongest σ70-RNAP binding site (consensus -10/-35 elements) using minimal thermodynamic binding energy.</li>
                <li><strong>Standard + Spacer</strong>: Adds penalties for non-canonical spacer lengths (≠17bp between -10/-35 elements) to the base model.</li>
                <li><strong>Standard + Spacer + Cumulative</strong>: Considers all potential binding configurations (not just strongest) with spacer penalties, integrating their combined thermodynamic effects.</li>
                <li><strong>Extended</strong>: Full biophysical model incorporating six structural features - multiple binding configurations, spacer effects, dinucleotide interactions, flanking sequences, DNA flexibility, and competitive non-productive binding.</li>
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
                <li>Brick plot visualization (.png)</li>
                <li>Predicted expression level ( P<sub>on</sub>) and confidence interval (95%) (.txt)</li>
              </ul>
            </div>
            <Typography variant="body2" paragraph>
            <strong>Sequence Limit:</strong> Registered users can input up to 100 sequences per month.
          </Typography>
        </Paper>
      </Fade>

      {results.image && (
        <Paper sx={{ p: 3, mt: 3, backgroundColor: '#fff' }}>
          <Typography variant="h6" gutterBottom>
            Analysis Results
          </Typography>
          
          {results.loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <img 
                src={results.image} 
                alt="Gene expression analysis" 
                style={{ 
                  maxWidth: '100%', 
                  height: 'auto',
                  borderRadius: '8px',
                  marginBottom: '16px'
                }} 
              />
              
              <Typography variant="body1" sx={{ 
                whiteSpace: 'pre-wrap',
                backgroundColor: '#f5f5f5',
                p: 2,
                borderRadius: '4px'
              }}>
                {results.analysis}
              </Typography>
            </>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default AlgoForm;