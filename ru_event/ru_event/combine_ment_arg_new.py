#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse

def merge(mentions_bio, args_bio, out):
    mentions = mentions_bio.strip().splitlines()
    args = args_bio.strip().splitlines()
    new = dict()
    nlist = []
    for line in args:
        if not line.strip():
            continue

        word, mention, _, _, tag = line.strip().split(' ')
        new[mention] = tag
    for i,l in enumerate(mentions):
        l = l.strip()       
        if l:
            m = l.split(' ')
            try:
                nlist.append(' '.join([m[0], m[1], m[2], new[l.split(' ')[1]], m[3]]) + '\n')
            except:
                nlist.append(' '.join([m[0], m[1], m[2], 'O', m[3]]) + '\n')
        else:
            nlist.append('\n')
    out.writelines(nlist)

#####
def runner(input_trigger_offset_file, input_edl_bio_file, output_file):
    with open(input_trigger_offset_file, 'r', encoding = 'utf-8') as mentfile,\
        open(input_edl_bio_file, 'r', encoding = 'utf-8') as argfile,\
        open(output_file,'w', encoding = 'utf-8') as outfile:
        
        merge(mentfile.read(), argfile.read(), outfile)

#####
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--input_trigger_offset_file", default="ann_data_m9/dryrun_0704/bio/uk_triggers_offset.bio",
        help="location of bio file with tagged triggers and offsets"
    )
    
    parser.add_argument(
        "--input_edl_bio_file", default="ann_data_m9/dryrun_0704/edl/uk/uk.nam+nom.tagged.bio",
        help="location of bio file with tagged entities"
    )
    
    parser.add_argument(
        "--output_file", default="ann_data_m9/dryrun_0704/bio/uk_merged.bio",
        help="location of output bio file after merging"
    )
    
    args = parser.parse_args()
    
    with open(args.input_trigger_offset_file, 'r', encoding = 'utf-8') as mentfile,\
        open(args.input_edl_bio_file, 'r', encoding = 'utf-8') as argfile,\
        open(args.output_file,'w', encoding = 'utf-8') as outfile:
        
        merge(mentfile.read(),argfile.read(), outfile)
