#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 26 21:44:49 2018

@author: samyaza
"""

import os
import sys
import json
import argparse

def create_cs(rsdpath, entity_cs_path, cspath, trig_offset_file, cnn_out_file):
    mentions = ''
    preds = []
    mention_dict = dict()
    arg = dict()
    ent = dict()
    typemap = dict()
    
    #
    minconf = 100
    maxconf = -1
    
    # cwd_path = os.getcwd()
    cwd_path = os.path.dirname(os.path.realpath(__file__))
    typefile = os.path.join(cwd_path, 'aida_types.txt')
    constraint_file = os.path.join(cwd_path, 'arg_type_constraints.json')

    #convert from old ontology used in annotation, to new ontology types
    with open(typefile, 'r', encoding = 'utf-8') as t:
        types = t.read().strip().split('\n')
        for typ in types:
            newt, oldt = typ.strip().split(' ')
            typemap[oldt] = newt
    
    #ontological constraints for arguments
    with open(constraint_file, 'r', encoding = 'utf-8') as t:
        constraints = json.load(t)
        constraints['Agent'] = ['PER', 'ORG', 'GPE']
        constraints['Plaintiff'] = ['PER']
        constraints['Adjudicator'] = ['PER']
        constraints['Investigatee'] = ['PER']
        constraints['Signer'] = ['PER']
        constraints['Broadcaster'] = ['PER', 'ORG', 'GPE']
        constraints['Territory'] = ['GPE', 'LOC']
        constraints['Person'] = ['PER']


    #create dictionary of entities        
    with open(entity_cs_path, 'r', encoding = 'utf-8') as entities_cs:
        entfile = entities_cs.read().split('\n')
        for line in entfile:
            details = line.split('\t')
            if len(details) == 3:
                enttype = details[2]
                entid = details[0]
            if len(details)>3:
                if entid == details[0]:
                    if details[3].split(':')[0] in ent:
                        ent[details[3].split(':')[0]][details[3]] = [details[0], enttype]
                    else:
                        ent[details[3].split(':')[0]] = dict()
                        ent[details[3].split(':')[0]][details[3]] = [details[0], enttype]
                else:
                    print("oops")
    
    #take results from trigger and argument models and combine
    with open(trig_offset_file, 'r', encoding = 'utf-8') as mentfile,\
            open(cnn_out_file, 'r', encoding = 'utf-8') as csvfile:
    
                
        preds = csvfile.read().strip().split('\n')
        
        mentions = mentfile.read().split('\n')
        predcount = 0    
        for ment in mentions:
            c = ment.split(' ')
            if len(c)>2:
                if '-' in c[-2]:
                    if any([',,,' in ment, '??' in ment, '[' in ment, ']' in ment, '``' in ment, '~' in ment, ')'in ment, '(' in ment, 'xxx' in ment, '_' in c[0], 'net.' in ment, '.net' in ment, '=' in ment, 'www.' in ment, '!!!' in ment, '+' in ment, '---' in ment, '::' in ment, '#' in ment, '@' in ment, 'http' in ment, '...' in ment, len(c[0]) <= 2, len(c[0]) >= 30]):
                          continue
                    file, offs = c[1].split(':')
                    if file not in mention_dict:
                        mention_dict[file] = dict()
                    start, end = offs.split('-')
                    with open(os.path.join(rsdpath,c[1].split(':')[0]+'.rsd.txt'), 'r', encoding='utf-8') as rsd:
                        text = rsd.read()[int(start):int(end) + 1]
                        # if text != c[0]:
                            # print(c[0], text)
                    mention_dict[file][str(c[1])] = [c[2].strip().split('-')[1], text, c[3].strip()[:5]]
    
        for line in preds:
            pred = line.strip().split('\t')
            if 'not_an_arg' in pred[1]:
                continue
            details = pred[2].split('/')[-1].replace('.txt','').split('_')
            try:
                offset = details[0] + ':' + details[3].split('-')[1]+'-'+details[4].split('-')[1]
            except:
                continue
            file = details[0]
            if file not in arg:
                arg[file] = dict()
            if offset in arg[file]:
            
                arg[file][str(offset)].append([ pred[1].split('-')[1], details[1].split('-')[1], details[2].split('-')[1], pred[3]])
            else:
                arg[file][str(offset)] = [ [pred[1].split('-')[1], details[1].split('-')[1], details[2].split('-')[1], pred[3]] ]
            predcount+=1

            
    coldstart = []        
    count = 0        
    errcount = 0
    
    #post-processing checks and rules
    for file in mention_dict.keys():

        for ment in mention_dict[file]:
            count = count+1
            coldstart.append(':Event_' + str(count).zfill(5) + '\t' + 'type\t' + typemap[mention_dict[file][ment][0].replace('_','.')] + '\n')
            trigtype = typemap[mention_dict[file][ment][0].replace('_','.')]
            coldstart.append(':Event_' + str(count).zfill(5) + '\t' + 'mention.actual' + '\t"' + mention_dict[file][ment][1] + '"\t' + ment + '\t' + mention_dict[file][ment][2] + '\n')
            coldstart.append(':Event_' + str(count).zfill(5) + '\t' + 'canonical_mention.actual' + '\t"' + mention_dict[file][ment][1] + '"\t' + ment + '\t' + mention_dict[file][ment][2] + '\n')
            
            if float(mention_dict[file][ment][2]) < minconf:
                minconf = float(mention_dict[file][ment][2])
            if float(mention_dict[file][ment][2]) > maxconf:
                maxconf = float(mention_dict[file][ment][2])
            
            if file in arg:
                if ment in arg[file]:
                    for a in arg[file][str(ment)]:
                        try:
                            entkey, enttype = ent[file][str(file+':' +a[1]+'-'+a[2])]
                        except:
                            errcount += 1 
                            continue
                        
                        if 'DeclareBankruptcy' in trigtype:
                            if a[0] not in ['Organization','Place']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Organization'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
                        
                        elif 'Business.End' in trigtype:
                            if a[0] not in ['Organization','Place']:
                                if enttype in ['ORG']:
                                    a[0] = 'Organization'
                                elif enttype in ['LOC', 'FAC', 'GPE']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue 
                        
                        elif 'Business.Merge' in trigtype:
                            if a[0] not in ['Organization','Place']:
                                if enttype in ['ORG']:
                                    a[0] = 'Organization'
                                elif enttype in ['LOC', 'FAC', 'GPE']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                         
    
                        elif 'Business.Start' in trigtype:
                            if a[0] not in ['Agent','Organization','Place']:
                                if enttype in ['ORG']:
                                    a[0] = 'Organization'
                                elif enttype in ['LOC', 'FAC', 'GPE']:
                                    a[0] = 'Place'
                                elif enttype in ['PER']:
                                    a[0] = 'Agent'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                         
    
                        elif 'Attack' in trigtype:
                            if a[0] not in ['Attacker','Instrument','Place', 'Target']:
                                if enttype in ['PER','ORG']:
                                    a[0] = 'Target'
                                elif enttype in ['LOC', 'FAC', 'GPE']:
                                    a[0] = 'Place'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Instrument'
                                else:
                                    continue
                            else:
                                if a[0] != 'Attacker' and a[0] != 'Target' and enttype in ['PER','ORG']:
                                    a[0] = 'Target'
                                if enttype not in constraints[a[0]]:
                                    continue    
    
                        elif 'Demonstrate' in trigtype:
                            if a[0] not in ['Demonstrator','Place']:
                                if enttype in ['PER','ORG']:
                                    a[0] = 'Demonstrator'
                                elif enttype in ['LOC', 'GPE', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue    
    
                        elif 'Broadcast' in trigtype:
                            if a[0] not in ['Audience','Broadcaster', 'Place', 'Participant']:
                                if enttype in ['PER','ORG', 'GPE']:
                                    a[0] = 'Broadcaster'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Contact.Contact' in trigtype or 'Correspondence' in trigtype or 'Meet' in trigtype:
                            if a[0] not in ['Participant', 'Place']:
                                if enttype in ['PER','ORG', 'GPE']:
                                    a[0] = 'Participant'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'DamageDestroy' in trigtype:
                            if a[0] not in ['Agent', 'Instrument', 'Place', 'Victim']:
                                if enttype in ['PER','ORG', 'GPE']:
                                    a[0] = 'Agent'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Instrument'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
                        
                        elif 'Agreements' in trigtype:
                            if a[0] not in ['Signer', 'Place']:
                                if enttype in ['GPE']:
                                    a[0] = 'Signer'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Legislate' in trigtype:
                            if a[0] not in ['Legislature', 'Place']:
                                if enttype in ['ORG']:
                                    a[0] = 'Legislature'
                                elif enttype in ['LOC', 'FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Spy' in trigtype:
                            if a[0] not in ['Agent', 'Beneficiary', 'Place', 'Target', '']:
                                if enttype in ['PER']:
                                    a[0] = 'Agent'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Beneficiary'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Vote' in trigtype:
                            if a[0] not in ['Candidate', 'Place', 'Voter']:
                                if enttype in ['PER', 'ORG']:
                                    a[0] = 'Candidate'
                                elif enttype in ['LOC','FAC', 'GPE']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Inspection.Artifact' in trigtype:
                            if a[0] not in ['Inspector', 'Place', 'Thing']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Inspector'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Thing'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Inspection.People' in trigtype:
                            if a[0] not in ['Inspector', 'Place', 'Person']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Inspector'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Acquit' in trigtype or 'Convict' in trigtype or 'Pardon' in trigtype or 'Sentence' in trigtype:
                            if a[0] not in ['Adjudicator', 'Defendant', 'Place']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Defendant'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Acquit' in trigtype:
                            if a[0] not in ['Adjudicator', 'Defendant', 'Place', 'Prosecutor']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Defendant'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'ArrestJail' in trigtype or 'Execute' in trigtype or 'ReleaseParole' in trigtype:
                            if a[0] not in ['Agent', 'Person', 'Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Person'
                                if enttype in ['ORG', 'GPE']:
                                    a[0] = 'Agent'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
                            
                        elif 'ChargeIndict' in trigtype or 'TrialHearing' in trigtype:
                            if a[0] not in ['Adjudicator', 'Defendant', 'Place', 'Prosecutor']:
                                if enttype in ['PER']:
                                    a[0] = 'Prosecutor'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                       
                            
                        elif 'Extradite' in trigtype:
                            if a[0] not in ['Agent', 'Destination', 'Origin', 'Person']:
                                if enttype in ['PER']:
                                    a[0] = 'Person'
                                if enttype in ['ORG', 'GPE']:
                                    a[0] = 'Agent'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Origin'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                        
                        
                        elif 'Fine' in trigtype:
                            if a[0] not in ['Adjudicator', 'Defendant', 'Place']:
                                if enttype in ['PER','ORG', 'GPE']:
                                    a[0] = 'Defendant'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                         
                            
                        elif 'Investigate' in trigtype:
                            if a[0] not in ['Investigatee', 'Investigator', 'Place']:
                                if enttype in ['PER','ORG', 'GPE']:
                                    a[0] = 'Investigatee'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                         
                            
                        elif 'Sue' in trigtype:
                            if a[0] not in ['Adjudicator', 'Defendant', 'Place', 'Plaintiff']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Defendant'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                        
                            
                        elif 'BeBorn' in trigtype or 'Divorce' in trigtype or 'Marry' in trigtype:
                            if a[0] not in ['Person','Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Person'
                                elif enttype in ['LOC','FAC', 'GPE']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                         
                            
                        elif 'Die' in trigtype or 'Injure' in trigtype:
                            if a[0] not in ['Agent','Instrument', 'Place', 'Victim']:
                                if enttype in ['PER']:
                                    a[0] = 'Victim'
                                elif enttype in ['LOC','FAC', 'GPE']:
                                    a[0] = 'Place'
                                elif enttype in ['ORG']:
                                    a[0] = 'Agent'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Instrument'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue   
    
                        elif 'Manufacture.Artifact' in trigtype:
                            if a[0] not in ['Artifact', 'Instrument', 'Manufacturer', 'Place']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Manufacturer'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Artifact'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'TransportArtifact' in trigtype:
                            if a[0] not in ['Agent', 'Artifact', 'Instrument', 'Destination', 'Origin']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Agent'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Destination'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Artifact'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'TransportPerson' in trigtype:
                            if a[0] not in ['Agent', 'Instrument', 'Destination', 'Origin']:
                                if enttype in ['PER']:
                                    a[0] = 'Person'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Agent'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Destination'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Instrument'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Elect' in trigtype:
                            if a[0] not in ['Elect', 'Elector', 'Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Elect'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Elector'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'EndPosition' in trigtype or 'StartPosition' in trigtype:
                            if a[0] not in ['Organization', 'Person', 'Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Person'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Organization'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Nominate' in trigtype:
                            if a[0] not in ['Nominator', 'Nominee', 'Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Nominee'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Nominator'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Nominate' in trigtype:
                            if a[0] not in ['Nominator', 'Nominee', 'Place']:
                                if enttype in ['PER']:
                                    a[0] = 'Nominee'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['ORG', 'GPE']:
                                    a[0] = 'Nominator'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'Transaction.Transaction' in trigtype or 'TransferMoney' in trigtype:
                            if a[0] not in ['Beneficiary', 'Giver', 'Place', 'Recipient']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Giver'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'TransferControl' in trigtype:
                            if a[0] not in ['Beneficiary', 'Giver', 'Place', 'Recipient', 'Territory']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Giver'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue
    
                        elif 'TransferOwnership' in trigtype:
                            if a[0] not in ['Beneficiary', 'Giver', 'Place', 'Recipient', 'Thing']:
                                if enttype in ['PER', 'ORG', 'GPE']:
                                    a[0] = 'Giver'
                                elif enttype in ['LOC','FAC']:
                                    a[0] = 'Place'
                                elif enttype in ['VEH', 'WEA']:
                                    a[0] = 'Thing'
                                else:
                                    continue
                            else:
                                if enttype not in constraints[a[0]]:
                                    continue                        
                        coldstart.append(':Event_' + str(count).zfill(5) + '\t' + typemap[mention_dict[file][ment][0].replace('_','.')] + '_' + a[0] + '.actual\t'+ent[file][str(ment.split(':')[0]+':' +a[1]+'-'+a[2])][0] + '\t' + ment.split(':')[0] + ':' + a[1] + '-' + a[2] + '\t' + a[3] + '\n')
                        if float(a[3]) < minconf:
                            minconf = float(a[3])
                        if float(a[3]) > maxconf:
                            maxconf = float(a[3])
    cs = open(cspath, 'w', encoding = 'utf-8')
    cs.writelines(coldstart)
    cs.close()

#####
def runner(rsdpath, entity_cs_path, cspath, trig_offset_file, cnn_out_file):
    create_cs(rsdpath, entity_cs_path, cspath, trig_offset_file, cnn_out_file)

#####
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--rsdpath", default='/Volumes/Ann/univ/blender/supervised/for_manling_ru_event/data/source/ru_all_rsd/',
        help="location of rsd files"
    )
    
    parser.add_argument(
        "--entity_cs_path", default='/Volumes/Ann/univ/blender/supervised/for_manling_ru_event/data/source/edl_results/ru.merged.cs',
        help="cs file from edl results"
    )
    
    parser.add_argument(
        "--cspath", default='/Volumes/Ann/univ/blender/supervised/for_manling_ru_event/results/ru_all.cs',
        help="output event cs file"
    )
    
    parser.add_argument(
        "--trig_offset_file", default='/Volumes/Ann/univ/blender/supervised/for_manling_ru_event/intermediate_files/ru_all_triggers_offset.bio',
        help="trigger extraction results with offsets"
    )
    
    parser.add_argument(
        "--cnn_out_file", default='/Volumes/Ann/univ/blender/supervised/for_manling_ru_event/intermediate_files/ru_all.tsv',
        help="tsv output from cnn"
    )

    args = parser.parse_args()
    create_cs(args.rsdpath, args.entity_cs_path, args.cspath, args.trig_offset_file, args.cnn_out_file)



