# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 22:44:01 2018

@author: Ananya
"""
import argparse
import pathlib
import sys
import os


def make_folders(types, outpath):
    for folder in types:
        # pathlib.Path(os.path.join(outpath,folder)).mkdir(exist_ok=True)
        os.makedirs(os.path.join(outpath,folder), exist_ok=True)
        
def create_files(rsd, input_merged_bio, output_folder):
    with open(input_merged_bio, 'r', encoding = 'utf-8') as file:
        bio = file.read()
        sentences = bio.strip().split('\n\n')
        sizesents = len(sentences)
        for i, sent in enumerate(sentences):
#            if i%1000 == 0:
#                print(i, '/', sizesents)
            startmentpos = -1
            endmentpos = -1
            startargpos = -1
            endargpos = -1
            trigstart = -1
            trigend = -1
            argstart = -1
            argend = -1
            
            foldername = output_folder
            
            end = False
            s = sent.strip().split('\n')
            for i, word in enumerate(s):
                if word.strip():
                    argtag = word.strip().split(' ')[3]
                    mentag = word.strip().split(' ')[2]
                    
                    if ('B-') in mentag:
                        conftag = word.strip().split(' ')[4].strip()
                        startmentpos = i
                        trigstart = word.strip().split(' ')[1].split(':')[1].split('-')[0]
                        ii = i
                        while s[ii].strip().split(' ')[2]!='O' and ii<len(s)-1:
                            trigend = s[ii].strip().split(' ')[1].split(':')[1].split('-')[1]
                            ii = ii+1
    
                    elif 'B-' in argtag:
                        startargpos = i
                        argstart = word.strip().split(' ')[1].split(':')[1].split('-')[0]
                        segment = ''
                        ii = i
                        while s[ii].strip().split(' ')[3]!='O' and ii<len(s)-1:
                            argend = s[ii].strip().split(' ')[1].split(':')[1].split('-')[1]
                            ii = ii+1
                            endargpos = ii
                        if startmentpos>=0:
                            if startmentpos<i:
                                for n in range(startmentpos,ii+1):
                                    with open(os.path.join(rsd,word.strip().split(' ')[1].split(':')[0]+'.rsd.txt'), 'r', encoding = 'utf-8') as rsdfile:
                                        segment = rsdfile.read()[int(trigstart):int(argend)]
                                if argstart != -1 and trigstart!=-1:
                                    with open(foldername+"/"+(word.strip().split(' ')[1].strip()).split(':')[0]\
                                              +'_argstart-'+ str(argstart)+'_argend-'+str(argend)\
                                              +'_trigstart-'+str(trigstart)+'_trigend-'+str(trigend)\
                                              +'_trigconf-'+str(conftag)\
                                              +'.txt', 'w', encoding = 'utf-8') as tmp:
                                        tmp.write(segment)
                                segment = ''
                        elif startmentpos == -1:
                            for n in range(i,len(s)):
                                if 'B-' in s[n].strip().split(' ')[2]:
                                    startmentpos = n
                                    trigstart = s[n].strip().split(' ')[1].split(':')[1].split('-')[0]
                                    conftag = s[n].strip().split(' ')[4].strip()
                                    m = n
                                    while s[m].strip().split(' ')[2]!='O' and m<len(s)-1:
                                        trigend = s[m].strip().split(' ')[1].split(':')[1].split('-')[1]
                                        m = m + 1
                                    for o in range(i,m+1):
                                        with open(os.path.join(rsd,word.strip().split(' ')[1].split(':')[0]+'.rsd.txt'), 'r', encoding = 'utf-8') as rsdfile:
                                            segment = rsdfile.read()[int(argstart):int(trigend)]
                            if argstart!=-1 and trigstart!=-1:
                                with open(foldername+"/"+(word.strip().split(' ')[1].strip()).split(':')[0]\
                                          +'_argstart-'+ str(argstart)+'_argend-'+str(argend)\
                                          +'_trigstart-'+str(trigstart)+'_trigend-'+str(trigend)\
                                          +'_trigconf-'+str(conftag)\
                                          +'.txt', 'w', encoding = 'utf-8') as tmp:
                                    tmp.write(segment)
                            segment = ''

#####
def runner(input_rsd_folder, input_merged_bio, out_folder_path):
    # default output flder
    cwd_path = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()
    # output_folder = os.path.join(cwd_path, 'intermediate_files/cnn_in/')
    output_folder = os.path.join(out_folder_path, 'cnn_in')
    argument_classes_file = os.path.join(cwd_path, 'argument_classes.txt')

    types = []
    print('Creating intermediate files for input to argument classifer....')
    with open(argument_classes_file,'r') as t:
        types = t.read().strip().split('\n')
    make_folders(types, output_folder)
    create_files(input_rsd_folder, input_merged_bio, os.path.join(output_folder,'business_endbus-Organization/'))

#####
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--input_rsd_folder", default="/source/uk_rsd/",
        help="location of rsd files"
    )
    
    parser.add_argument(
        "--input_merged_bio", default="bio/uk_merged.bio",
        help="location of bio file with triggers and entities merged"
    )
    
    parser.add_argument(
        "--output_folder", default="intermediate_files/cnn_in/",
        help="location of output files"
    )
    
    args = parser.parse_args()
    
    types = []
    print('Creating intermediate files for input to argument classifer....')
    with open('argument_classes.txt','r') as t:
        types = t.read().strip().split('\n')
    make_folders(types, args.output_folder)
    create_files(args.input_rsd_folder, args.input_merged_bio, os.path.join(args.output_folder,'business_endbus-Organization/'))
    
    