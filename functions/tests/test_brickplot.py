#!/usr/bin/env python3
"""
Test script for brickplot functionality
"""
import os
import sys
import logging
from BrickPlotter import BrickPlotter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_brickplot_generation():
    """Test basic brickplot generation"""
    try:
        # Test sequence
        test_sequence = "ATCGATCGATCGATCGATCG"
        
        # Check if model file exists
        model_path = "models/fitted_on_Pr/model_[3]_stm+flex+cumul+rbs.dmp"
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return False
        
        # Create brickplotter
        brickplotter = BrickPlotter(
            model=model_path,
            output_folder="test_output",
            is_plus_one=True,
            is_rc=False,
            max_value=-2.5,
            min_value=-6,
            threshold=-2.5,
            is_prefix_suffix=True
        )
        
        # Generate brickplot
        result = brickplotter.get_brickplot(test_sequence)
        
        # Check result structure
        required_keys = ['image_base64', 'matrix', 'statistics', 'sequence_length', 'sequence']
        for key in required_keys:
            if key not in result:
                logger.error(f"Missing key in result: {key}")
                return False
        
        # Check statistics
        stats = result['statistics']
        required_stats = ['min_energy', 'max_energy', 'mean_energy', 'best_position']
        for stat in required_stats:
            if stat not in stats:
                logger.error(f"Missing statistic: {stat}")
                return False
        
        logger.info("✓ Brickplot generation test passed")
        logger.info(f"Generated brickplot for sequence: {test_sequence}")
        logger.info(f"Matrix shape: {len(result['matrix'])}x{len(result['matrix'][0]) if result['matrix'] else 'empty'}")
        logger.info(f"Statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Brickplot generation test failed: {e}")
        return False

def test_file_processing():
    """Test file processing functionality"""
    try:
        # Create test CSV file
        test_csv_content = "seq1,ATCGATCGATCG\nseq2,GCTAGCTAGCTA"
        test_csv_file = "test_sequences.csv"
        
        with open(test_csv_file, 'w') as f:
            f.write(test_csv_content)
        
        # Test CSV processing
        brickplotter = BrickPlotter(
            model="models/fitted_on_Pr/model_[3]_stm+flex+cumul+rbs.dmp",
            output_folder="test_output"
        )
        
        result = brickplotter.get_brickplot(test_csv_file)
        
        # Clean up
        os.remove(test_csv_file)
        
        if result and 'sequence' in result:
            logger.info("✓ File processing test passed")
            return True
        else:
            logger.error("✗ File processing test failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ File processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting brickplot functionality tests...")
    
    tests = [
        test_brickplot_generation,
        test_file_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 