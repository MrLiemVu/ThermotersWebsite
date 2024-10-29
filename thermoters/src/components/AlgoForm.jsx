// src/components/AlgoForm.js
import React, { useState } from 'react';
import {
  TextField, Select, MenuItem, Button, Box, FormControl, InputLabel,
  FormGroup, FormControlLabel, Checkbox, Switch
} from '@mui/material';
import { addDoc, collection } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { db } from '../../firebaseConfig'; // Ensure this path is correct based on your project structure

const AlgoForm = () => {
  // State for form fields
  const [formData, setFormData] = useState({
    jobtitle: '',
    sequence: '',
    predictors: {
        standard: false,
        standardSpacerCumulative: false,
        standardSpacer: false,
      },
    brickplot: false,
    uploadedAt: new Date()
  });

  // Handle input change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value
    }));
  };

  // Handle checkbox change for predictors
  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      predictors: {
        ...prevData.predictors,
        [name]: checked,
      },
    }));
  };

  // Handle toggle switch change for brickplot
  const handleToggleChange = (e) => {
    const { checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      brickplot: checked,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    const user = auth.currentUser;
    const submissionData = {
      ...formData,
      uploadedAt: new Date(), // Capture current date and time on submit
    };

    try {
      const docRef = await addDoc(collection(db, "users", user.uid, "jobhistory"), submissionData);
      console.log("Document written with ID: ", docRef.id);
      // Reset form after successful submission
      setFormData({
        jobtitle: '',
        predictors: {
          standard: false,
          standardSpacerCumulative: false,
          standardSpacer: false,
        },
        filetype: '',
        brickplot: false,
      });
    } catch (error) {
      console.error("Error adding document: ", error);
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        width: '100%',
        maxWidth: 500,
        mx: 'auto', // center form horizontally
        mt: 0, // add some top margin
        p: 3, // add padding
        border: '1px solid #ccc', // optional border for visibility
        borderRadius: 2,
      }}
    >
      {/* Job Title Input */}
      <TextField
        label="Job Title"
        name="jobtitle"
        value={formData.jobtitle}
        onChange={handleChange}
        variant="outlined"
        required
        fullWidth
      />

      {/* Sequence Input */}
      <TextField
        label="Sequence"
        name="sequence"
        value={formData.sequence}
        onChange={handleChange}
        variant="outlined"
        multiline
        rows={4}
        required
        fullWidth
      />


      {/* Checkbox Group for Predictors */}
      <FormControl component="fieldset">
        <FormGroup>
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.predictors.standard}
                onChange={handleCheckboxChange}
                name="standard"
              />
            }
            label="Standard"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.predictors.standardSpacerCumulative}
                onChange={handleCheckboxChange}
                name="standardSpacerCumulative"
              />
            }
            label="Standard + Spacer + Cumulative"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.predictors.standardSpacer}
                onChange={handleCheckboxChange}
                name="standardSpacer"
              />
            }
            label="Standard + Spacer"
          />
        </FormGroup>
      </FormControl>

      {/* Dropdown for File Type */}
      <FormControl fullWidth>
        <InputLabel id="filetype-label">File Type</InputLabel>
        <Select
          labelId="filetype-label"
          name="filetype"
          value={formData.filetype}
          onChange={handleChange}
          required
        >
          <MenuItem value="csv">Excel spreadsheet (.csv)</MenuItem>
          <MenuItem value="fna">FASTA nucleic acid (.fna)</MenuItem>
          <MenuItem value="ffn">FASTA nucleotide of gene regions (.ffn)</MenuItem>
          <MenuItem value="faa">FASTA amino acid (.faa)</MenuItem>
          {/* Add more file types as needed */}
        </Select>
      </FormControl>

      {/* Toggle Switch for Brickplot */}
      <FormControlLabel
        control={
          <Switch
            checked={formData.brickplot}
            onChange={handleToggleChange}
            name="brickplot"
            color="primary"
          />
        }
        label="Brickplot"
      />

      <Button type="submit" variant="contained" color="primary" fullWidth>
        Submit
      </Button>
    </Box>
  );
};

export default AlgoForm;