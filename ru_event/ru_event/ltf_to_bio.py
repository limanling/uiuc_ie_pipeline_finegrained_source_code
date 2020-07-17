# -*- coding: utf-8 -*-
"""
Created on Sat Sep  1 13:36:50 2018

@author: Ananya
"""
import argparse
import os
import xml.etree.ElementTree as ET


def make_bio_files(ltf_folder_path, out_file_path):
    lines = []
    files = []
    lines_offset = []
    out_file = os.path.join(out_file_path, 'ru_all.bio')
    dryrun_files = os.listdir(ltf_folder_path)
    for ltffile in dryrun_files:
        if '._' not in ltffile:
            files.append(ltffile.split('.')[0])
        
        
    for fil in files:
        file = fil.strip()
        file = os.path.join(ltf_folder_path, file + '.ltf.xml')
        with open(file, 'r', encoding = 'utf-8') as mafile:
            ma = mafile.read()
            root = ET.fromstring(ma)
            for seg in root[0][0]:
                for child in seg:
                    if child.tag != 'TOKEN':
                        continue
                    token = child.text.strip()
                    start = child.get('start_char')
                    end = child.get('end_char')
                    lines_offset.append(token + ' ' + fil+':'+start+'-'+end + ' ' + 'O')
                    lines.append(token + ' ' + 'O')
                lines[-1] = lines[-1] + '\n'
                lines_offset[-1] = lines_offset[-1] + '\n'
    
    with open(out_file, 'w', encoding = 'utf-8') as bio:
        bio.write('\n'.join(lines))
    
    with open(out_file.replace('.bio','_offset.bio'), 'w', encoding = 'utf-8') as bio:
        bio.write('\n'.join(lines_offset))

#####
def runner(ltf_folder_path, out_file_path):
    make_bio_files(ltf_folder_path, out_file_path)


#####
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--ltf_folder_path", default="/Volumes/Ann/univ/blender/supervised/ann_data_m9/dryrun_0704_/source/uk",
        help="location of folder containing ltf files"
    )
    
    parser.add_argument(
        "--out_file_path", default="/Volumes/Ann/univ/blender/supervised/ann_data_m9/dryrun_0704_/bio/uk.bio",
        help="output file path"
    )
    
    args = parser.parse_args()
    
    make_bio_files(args.ltf_folder_path, args.out_file_path)
    