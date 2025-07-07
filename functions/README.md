# Thermoters Firebase Functions

This directory contains the Firebase Functions backend for the Thermoters gene expression prediction platform.

## Structure

```
functions/
├── main.py                 # Main Firebase Functions entry point
├── BrickPlotter.py        # Core brickplot generation class
├── requirements.txt        # Python dependencies
├── test_brickplot.py      # Test script for brickplot functionality
├── utils/                 # Utility functions
│   ├── general_functions.py
│   ├── model_functions.py
│   └── __init__.py
└── models/                # Pre-trained model files
    ├── fitted_on_Pr/
    └── fitted_on_Pr.Pl.36N/
```

## Key Features

### 1. BrickPlotter Class
- **Complete Implementation**: Full brickplot generation algorithm
- **File Support**: Handles CSV, FASTA, FNA, FFN, FAA file formats
- **Error Handling**: Comprehensive validation and error reporting
- **Visualization**: Generates base64-encoded PNG images
- **Statistics**: Provides detailed binding energy statistics

### 2. Firebase Functions
- **submit_job**: Main API endpoint for sequence analysis
- **create_user_document**: User management on signup
- **ping**: Health check endpoint

### 3. File Processing
- **CSV Support**: Extracts sequences from CSV files
- **FASTA Support**: Handles multiple FASTA formats
- **Validation**: Ensures sequences contain only valid nucleotides (ACGTU)

## API Endpoints

### POST /submit_job
Submit a DNA sequence for brickplot analysis.

**Request Body:**
```json
{
  "sequence": "ATCGATCGATCGATCG",
  "model": "models/fitted_on_Pr/model_[3]_stm+flex+cumul+rbs.dmp",
  "jobTitle": "My Analysis",
  "isPlusOne": true,
  "isRc": false,
  "maxValue": -2.5,
  "minValue": -6,
  "threshold": -2.5,
  "isPrefixSuffix": true
}
```

**Response:**
```json
{
  "message": "Job completed successfully",
  "jobId": "job_id",
  "brickplot": {
    "image_base64": "base64_encoded_png",
    "matrix": [[energy_values]],
    "statistics": {
      "min_energy": -5.2,
      "max_energy": -2.1,
      "mean_energy": -3.8,
      "best_position": {
        "spacer_config": 2,
        "sequence_position": 15
      }
    },
    "sequence_length": 16,
    "sequence": "ATCGATCGATCGATCG"
  }
}
```

## Testing

Run the test script to verify functionality:

```bash
cd functions
python test_brickplot.py
```

## Dependencies

Key dependencies include:
- `firebase-admin`: Firebase integration
- `biopython`: Biological sequence processing
- `numpy`: Numerical computations
- `matplotlib`: Plot generation
- `scikit-learn`: Machine learning utilities
- `scipy`: Scientific computing

## Error Handling

The system includes comprehensive error handling:
- **Input Validation**: Checks for valid DNA sequences
- **File Validation**: Verifies file formats and content
- **Model Validation**: Ensures model files exist and are valid
- **User Limits**: Enforces monthly usage limits
- **Graceful Degradation**: Returns meaningful error messages

## Security

- **Authentication**: Firebase Auth integration
- **User Isolation**: Users can only access their own data
- **Input Sanitization**: Validates all user inputs
- **Rate Limiting**: Monthly usage limits per user

## Performance

- **Efficient Processing**: Optimized brickplot generation
- **Image Compression**: Base64 encoding for easy transmission
- **Caching**: Firebase caching for repeated requests
- **Background Processing**: Non-blocking job processing

## Deployment

Deploy to Firebase Functions:

```bash
firebase deploy --only functions
```

## Monitoring

- **Logging**: Comprehensive logging throughout
- **Error Tracking**: Detailed error reporting
- **Performance Metrics**: Execution time tracking
- **Usage Analytics**: User activity monitoring 