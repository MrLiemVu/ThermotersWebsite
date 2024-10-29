import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import brickplotImage from '../assets/brickplot_explanation.png';

const HomePage = () => {
  return (
    <Box
      sx={{
        mx: 'auto',
        mt: '1%',
        p: '5%',
        maxWidth: '50%'
      }}
    >
      {/* Title and Subtitle */}
      <Box textAlign="center" mb={4}>
        <Typography variant="h3" fontWeight="bold" gutterBottom>
          Gene Expression Prediction
        </Typography>
        <Typography variant="h5" color="textSecondary">
          Predicting bacterial sigma70 binding sites and constitutive expression levels
        </Typography>
      </Box>

      {/* Introductory Text */}
      <Box mb={4}>
        <Typography variant="body1" paragraph>
          At Lagator Lab, we developed a statistical thermodynamics model to identify binding of E. coli
          sigma70 along any sequence and predict constitutive expression levels from any sequence given
          sigma70 binding affinities.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Paper: Mato Lagator*, Srdjan Sarikas*, Magdalena Steinrueck, David Toledo-Aparicio, Jonathan P Ballback, 
          Calin C Guet; Gasper Tkacik (2022). Predicting bacterial promoter function and evolution from random 
          sequences. eLife 11:e64543.{' '}
          <a href="https://doi.org/10.7554/eLife.64543" target="_blank" rel="noopener noreferrer">
            https://doi.org/10.7554/eLife.64543
          </a>
        </Typography>
      </Box>

      {/* Description Cards */}
      <Grid container spacing={3} mb={4}>
        {/* First Card */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, backgroundColor: '#f3e5f5' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Identify binding of sigma70
            </Typography>
            <Typography variant="body2" mb={2}>
              For each sequence, a "brick plot" will be determined. The brick plot shows the energy of sigma70 binding
              at every possible position in the sequence, with five different spacer configurations (capturing the
              natural variability in the length of the spacer between the -10 and -35 "feet" of RNA polymerase).
            </Typography>
            <Typography variant="body2" mb={2}>
              Each pixel in the brick plot corresponds to the most downstream DNA residue contacted by polymerase
              (i.e., the part of the -10 binding region that is closest to the transcriptional start site). The color of
              the pixel corresponds to the binding energy (lower energy = stronger binding).
            </Typography>
          </Paper>
        </Grid>

        {/* Second Card */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, backgroundColor: '#f3e5f5' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Predict constitutive expression levels
            </Typography>
            <Typography variant="body2" mb={2}>
              There are three versions of the algorithm to convert sigma factor binding energies (contained in the brick
              plot) into predictions of expression levels (Pon):
            </Typography>
            <ul>
              <li>
                <Typography variant="body2">Standard model: estimates expression level only from a single sigma70 binding site with the lowest binding energy.</Typography>
              </li>
              <li>
                <Typography variant="body2">Standard + spacer: accounts for energy penalties with different spacer configurations.</Typography>
              </li>
              <li>
                <Typography variant="body2">Extended model (recommended): accounts for all possible sigma70 binding sites with energy associated with different spacer configurations.</Typography>
              </li>
            </ul>
          </Paper>
        </Grid>
      </Grid>

      {/* Illustration Section */}
      <Box textAlign="center" sx={{minWidth: 1250, maxWidth: '70%', mx: 'auto', mt: 4, p: 3, backgroundColor: '#f3e5f5', borderRadius: '8px', justifyContent: 'center'}}>
        <Typography variant="h6" fontWeight="bold" mb={2}>
          Brick plot illustration
        </Typography>
        <img
          src={brickplotImage} // replace with your actual image path
          alt="Brick plot illustration"
          style={{ minWidth: 1000, maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
        />
        <Typography variant="body2" color="textSecondary" mt={2}>
          Funded by the Welcome Trust and the Royal Society fellowship to ML (Grant Number 216779/Z/19/Z).
        </Typography>
      </Box>
    </Box>
  );
};

export default HomePage;