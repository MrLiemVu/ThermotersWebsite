from Bio.Seq import Seq
import os, copy
import numpy as np
from sys import path as syspath
import matplotlib.pyplot as plt
import pickle
syspath.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.general_functions import *
from utils.model_functions import *

BASES = "acgt"
LETTER_TO_INDEX = dict(zip(BASES, range(4)))

class BrickPlotter:
    '''
    Class for visualization of brickplot
    '''
    def __init__(self, model, output_folder, is_plus_one=True, is_rc=False, 
                 max_value=-2.5, min_value=-6, is_high_to_default=False,
                 threshold=-2.5, is_prefix_suffix=True):
        
        with open(model,"rb") as f:
            self.model = pickle.load(f, encoding="latin1")
            
        if is_plus_one: # True - a brick points to +1; False - points to -40
            self.shift = 40
        else:
            self.shift = 0
        self.is_rc = is_rc # True - reverse complement; False - original sequence
        self.max_value = max_value # maximum value for the color map
        self.min_value = min_value # minimum value for the color map
        self.is_high_to_default = is_high_to_default # If True, visualize brickplot values > treshold as default value
        self.threshold = threshold
        self.is_prefix_suffix = is_prefix_suffix # True - add Gs to the begining and end of each sequence to make it equal length and space for matrix
        
        self.default_value = self.max_value
        self.color_map = "hot"
        self.output_folder = output_folder
    
    def get_brickplot(self, filepath):
        '''
        Main function to get brickplot
        
        Args:
            filepath (str): path to the file with sequences
        
        Returns:
            None
        '''
        
        # 1. Read Sequences
        dict_seqs, max_seq_len = self.read_sequence_file(filepath)

        # 2. Preprocess
        num_unified_seqs, seq_ids, unified_seqs_dict = self.preprocess(dict_seqs, max_seq_len)
        
        # 3. Initialize Model
        leftFoot, rightFoot = self.model["matrices"]
        defaultSpacer       = self.model["Layout"][1]
        spacerFlexibility   = self.model["spFlex"]
        spacerPenalties     = self.model["sp.penalties"] 
        matrix = np.vstack([
                            leftFoot,
                            np.ones((defaultSpacer,4))*np.nan,
                            rightFoot
                        ])
        
        # 4. Get Bricks
        bricks = getBricks(
            twoMatrices     = [leftFoot, rightFoot],
            minSpacer       = defaultSpacer - spacerFlexibility, # minimal spacer
            spacerPenalties = spacerPenalties,
            sequences       = num_unified_seqs
        )
        
        # 5. Get Brickplot
        for i in range(len(num_unified_seqs)):
            curr_seq = unified_seqs_dict[seq_ids[i]][self.shift:-matrix.shape[0]-1]
            # print(curr_seq)
            # print('')
            # print('extended seg_len = ' + str(len(curr_seq)))
            theBrick = bricks.T[i]
            
            if self.is_high_to_default:
                display_bricks = self.remove_high_values(theBrick)
            else:
                display_bricks = theBrick
            
            plt.figure(figsize=(40,3))
            plt.imshow(display_bricks.T[:,:display_bricks.shape[0]-self.shift+1], cmap=self.color_map)
            plt.title(seq_ids[i])
            plt.yticks(range(5), np.arange(5)-2, fontsize=15)
            plt.xticks(range(len(curr_seq)), [char for char in curr_seq], fontsize=10)
            plt.clim([self.min_value, self.max_value])
            plt.ylabel('spacer\nflex', fontsize=15)
            plt.gca().set_aspect("auto")
            plt.colorbar()
            plt.savefig(self.output_folder + "/" + seq_ids[i] + '.pdf') 
    
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

    '''
    READING FUNCTIONS
    '''
    
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
        