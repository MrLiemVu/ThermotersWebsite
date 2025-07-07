from Bio.Seq import Seq
import os
import copy
import numpy as np
from sys import path as syspath
import matplotlib.pyplot as plt
import pickle
import base64
from io import BytesIO
import re
import logging

# Add parent directory to path to allow utils import
syspath.append(os.path.join(os.path.dirname(__file__), 'utils'))
from general_functions import *
from model_functions import *

BASES = "acgt"
LETTER_TO_INDEX = dict(zip(BASES, range(4)))

logger = logging.getLogger(__name__)

class BrickPlotter:
    '''
    Class for visualization of brickplot
    '''
    def __init__(self, model, output_folder, is_plus_one=True, is_rc=False, 
                 max_value=-2.5, min_value=-6,
                 threshold=-2.5, is_prefix_suffix=True):
        
        try:
            with open(model, "rb") as f:
                self.model = pickle.load(f, encoding="latin1")
        except Exception as e:
            logger.error(f"Failed to load model from {model}: {e}")
            raise ValueError(f"Invalid model file: {model}")
            
        if is_plus_one:
            self.shift = 40
        else:
            self.shift = 0
        self.is_rc = is_rc # True - reverse complement; False - original sequence
        self.max_value = max_value # maximum value for the color map
        self.min_value = min_value # minimum value for the color map
        self.threshold = threshold
        self.is_prefix_suffix = is_prefix_suffix # True - add Gs to the beginning and end of each sequence to make it equal length and space for matrix
        
        self.default_value = self.max_value
        self.color_map = "hot"
        self.output_folder = output_folder
    
    def get_brickplot(self, input_data: str) -> dict:
        """Generate brickplot for a DNA sequence"""
        try:
            if os.path.exists(input_data):
                # Input is a file path
                file_ext = os.path.splitext(input_data)[1].lower()
                with open(input_data, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if file_ext == '.csv':
                    sequences = self._process_csv(content)
                elif file_ext in ['.fasta', '.fna', '.ffn', '.faa']:
                    sequences = self._process_fasta(content)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                
                if not sequences:
                    raise ValueError("No valid sequences found in file")
                sequence = sequences[0]
            else:
                # Input is direct sequence
                sequence = input_data.upper().replace(' ', '')
            
            # Validate sequence
            if not re.match(r'^[ACGTU]+$', sequence):
                raise ValueError("Invalid characters in sequence")
            
            # Generate the brickplot
            return self._generate_plot(sequence)
            
        except Exception as e:
            logger.error(f"Error generating brickplot: {e}")
            raise
    
    def preprocess(self, dict_seqs, max_seq_len):
        '''
        Preprocess sequences: unify by length, convert to numbers
        
        Args:
            dict_seqs (dict): dictionary of sequences
            max_seq_len (int): maximum length of sequences
        
        Returns:
            num_unified_seqs (np.array): list of Int arrays made from Sequences unified by length
            seq_ids (list): list of seq_ids
            unified_seqs_dict (dict): dictionary of unified sequences
        '''
        unified_seqs_dict = {}
        for seq_id in dict_seqs:
            seq = dict_seqs[seq_id]
            if self.is_prefix_suffix:
                prefix = str('g'*(max_seq_len - len(seq)+self.shift+5))
                suffix = str('g'*(32+2+self.shift))
                unified_seqs_dict[seq_id] = (prefix+seq+suffix).lower()
            else:
                unified_seqs_dict[seq_id] = seq.lower()
                
                
        # Seqs as numbers: 1) list of Int arrays made from Sequences unified by length, 2) list of seq_ids     
        num_unified_seqs = []
        seq_ids = []
        for seq_id in unified_seqs_dict:
            seq_ids.append(seq_id)
        num_unified_seqs = np.array([np.array([LETTER_TO_INDEX[l] for l in s]) for s in unified_seqs_dict.values()])  
        return num_unified_seqs, seq_ids, unified_seqs_dict
    
    def remove_high_values(self, brick_in):
        '''
        Make values > threshold to be default value (for better visualization)
        
        Args:
            brick_in (np.array): brickplot matrix
        
        Returns:
            brick_out (np.array): brickplot matrix with values > treshold set to default value
        '''
        brick_out = copy.deepcopy(brick_in)
        for i in range(brick_in.shape[0]):
            for j in range(brick_in.shape[1]):
                if brick_in[i,j] > self.threshold:
                    brick_out[i,j] = self.default_value
        return brick_out

    def _generate_plot(self, sequence):
        """Generate brickplot visualization for a DNA sequence"""
        try:
            # Convert sequence to numerical representation
            seq_numeric = np.array([LETTER_TO_INDEX[base.lower()] for base in sequence])
            
            # Create sequence dictionary for processing
            seq_dict = {"sequence": seq_numeric.reshape(1, -1)}
            
            # Get brickplot data using the model
            brick_data = getBrickDict(
                seq_dict,
                self.model,
                dinucl=False,
                subtractChemPot=True,
                useChemPot="chem.pot",
                makeLengthConsistent=False
            )
            
            # Extract the brickplot matrix
            brick_matrix = brick_data["sequence"]
            
            # Remove high values for better visualization
            brick_matrix = self.remove_high_values(brick_matrix)
            
            # Generate the plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create the heatmap
            im = ax.imshow(brick_matrix, cmap=self.color_map, 
                          vmin=self.min_value, vmax=self.max_value,
                          aspect='auto', interpolation='nearest')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Binding Energy (kcal/mol)', rotation=270, labelpad=20)
            
            # Set labels and title
            ax.set_xlabel('Sequence Position')
            ax.set_ylabel('Spacer Configuration')
            ax.set_title('Sigma70 Binding Energy Brickplot')
            
            # Convert plot to base64 string
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            # Calculate summary statistics
            min_energy = np.min(brick_matrix)
            max_energy = np.max(brick_matrix)
            mean_energy = np.mean(brick_matrix)
            
            # Find best binding positions
            best_positions = np.unravel_index(np.argmin(brick_matrix), brick_matrix.shape)
            
            return {
                "image_base64": image_base64,
                "matrix": brick_matrix.tolist(),
                "statistics": {
                    "min_energy": float(min_energy),
                    "max_energy": float(max_energy),
                    "mean_energy": float(mean_energy),
                    "best_position": {
                        "spacer_config": int(best_positions[0]),
                        "sequence_position": int(best_positions[1])
                    }
                },
                "sequence_length": len(sequence),
                "sequence": sequence
            }
            
        except Exception as e:
            logger.error(f"Error in _generate_plot: {e}")
            raise ValueError(f"Failed to generate brickplot: {e}")

    def _process_csv(self, content):
        """Process CSV content to extract DNA sequences"""
        sequences = []
        lines = content.strip().split('\n')
        
        for line in lines:
            if line.strip():
                # Try to extract sequence from CSV format
                parts = line.split(',')
                if len(parts) >= 2:
                    # Assume second column contains sequence
                    seq = parts[1].strip().upper()
                    if re.match(r'^[ACGTU]+$', seq):
                        sequences.append(seq)
                elif len(parts) == 1:
                    # Single column, assume it's the sequence
                    seq = parts[0].strip().upper()
                    if re.match(r'^[ACGTU]+$', seq):
                        sequences.append(seq)
        
        return sequences

    def _process_fasta(self, content):
        """Process FASTA content to extract DNA sequences"""
        sequences = []
        current_seq = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('>'):
                # Save previous sequence if exists
                if current_seq:
                    seq = ''.join(current_seq).upper()
                    if re.match(r'^[ACGTU]+$', seq):
                        sequences.append(seq)
                    current_seq = []
            else:
                current_seq.append(line.upper().replace(' ', ''))
        
        # Add the last sequence
        if current_seq:
            seq = ''.join(current_seq).upper()
            if re.match(r'^[ACGTU]+$', seq):
                sequences.append(seq)
        
        return sequences

    def read_sequence_file(self, filepath):
        '''
        Directs to the appropriate reading function based on the file extension
        '''
        filetype = filepath.split('.')[-1]
        match filetype:
            case "fasta":
                dict_seqs, max_seq_len = self.read_fasta(filepath)
            case "csv":
                dict_seqs, max_seq_len = self.read_csv(filepath)
            case "fna": # FASTA Nucleic Acids
                dict_seqs, max_seq_len = self.read_fna(filepath)
            case "ffn": # FASTA Nucleotides of Gene Regions
                dict_seqs, max_seq_len = self.read_ffn(filepath)
            case "faa": # FASTA Amino Acids
                dict_seqs, max_seq_len = self.read_faa(filepath)
            case _:
                print("Filetype not supported")
        return dict_seqs, max_seq_len

    def read_fasta(self, fasta_filepath):
        ''' Read FASTA file '''
        fasta_reader = open(fasta_filepath, 'r')
        dict_seqs = {}
        max_seq_len = 0
        for line in fasta_reader:
            if line.startswith('>'):
                seq_id = line.strip('>').strip()
                # print(seq_id)
            else:
                seq = line.strip('"').strip()
                if seq == '':
                    continue
                else:
                    if self.is_rc:
                        seq = str(Seq(seq).reverse_complement())
                # print('sequence length = ' + str(len(seq)))
                if max_seq_len < len(seq):
                    max_seq_len = len(seq)
                # print(seq)
                dict_seqs[seq_id] = seq
        fasta_reader.close()
        return dict_seqs, max_seq_len

    def read_csv(self, csv_filepath):
        ''' Read CSV file '''
        csv_reader = open(csv_filepath, 'r')
        dict_seqs = {}
        max_seq_len = 0
        for line in csv_reader:
            seq_id, seq = line.strip().split(',')
            if self.is_rc:
                seq = str(Seq(seq).reverse_complement())
            if max_seq_len < len(seq):
                max_seq_len = len(seq)
            dict_seqs[seq_id] = seq
        csv_reader.close()
        return dict_seqs, max_seq_len

    def read_fna(self, fna_filepath):
        ''' Read FASTA Nucleic Acids file '''
        fna_reader = open(fna_filepath, 'r')
        dict_seqs = {}
        max_seq_len = 0
        for line in fna_reader:
            if line.startswith('>'):
                seq_id = line.strip('>').strip()
            else:
                seq = line.strip('"').strip()
                if seq == '':
                    continue
                else:
                    if self.is_rc:
                        seq = str(Seq(seq).reverse_complement())
                if max_seq_len < len(seq):
                    max_seq_len = len(seq)
                dict_seqs[seq_id] = seq
        fna_reader.close()
        return dict_seqs, max_seq_len

    def read_ffn(self, ffn_filepath):
        ''' Read FASTA Nucleotides of Gene Regions file '''
        ffn_reader = open(ffn_filepath, 'r')
        dict_seqs = {}
        max_seq_len = 0
        for line in ffn_reader:
            if line.startswith('>'):
                seq_id = line.strip('>').strip()
            else:
                seq = line.strip('"').strip()
                if seq == '':
                    continue
                else:
                    if self.is_rc:
                        seq = str(Seq(seq).reverse_complement())
                if max_seq_len < len(seq):
                    max_seq_len = len(seq)
                dict_seqs[seq_id] = seq
        ffn_reader.close()
        return dict_seqs, max_seq_len

    def read_faa(self, faa_filepath):
        ''' Read FASTA Amino Acids file '''
        faa_reader = open(faa_filepath, 'r')
        dict_seqs = {}
        max_seq_len = 0
        for line in faa_reader:
            if line.startswith('>'):
                seq_id = line.strip('>').strip()
            else:
                seq = line.strip('"').strip()
                if seq == '':
                    continue
                else:
                    if self.is_rc:
                        seq = str(Seq(seq).reverse_complement())
                if max_seq_len < len(seq):
                    max_seq_len = len(seq)
                dict_seqs[seq_id] = seq
        faa_reader.close()
        return dict_seqs, max_seq_len
        