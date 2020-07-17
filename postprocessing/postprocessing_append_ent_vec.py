from rdflib import Graph, plugin, URIRef, Namespace
from rdflib.serializer import Serializer
from rdflib.namespace import RDF
import sys
sys.path.append("/nas/data/m1/lim22/aida/aif0330/AIDA-Interchange-Format/python")
sys.path.append("/nas/data/m1/lim22/aida/aif0330/AIDA-Interchange-Format/python/aida_interchange")
from aida_interchange import aifutils

import os
import ujson as json
import traceback
import numpy as np
from collections import defaultdict

# num = sys.argv[1]
hypo = sys.argv[1]
run = sys.argv[2]
num = int(sys.argv[3])
total = int(sys.argv[4])

# # result_path = "/nas/data/m1/lim22/aida2019/LDC2019E42/0628/final_clean3/GAIA_1/" #% language_id
# input_folder = '/nas/data/m1/lim22/aida2019/TA1b_eval/merged_CU_RPI_USC_TA1b_20190712/merged_ttl_%s_%s_rel_evt_ent' % (hypo.split('_')[-1], run)
# output_folder = '/nas/data/m1/lim22/aida2019/TA1b_eval/merged_CU_RPI_USC_TA1b_20190712/merged_ttl_%s_%s_rel_evt_ent_veh' % (hypo.split('_')[-1], run)
# # output_folder_json = os.path.join(result_path, "INTER-TA_entityvec_json_tmp/%s") %num
# ent_vec_dir = '/nas/data/m1/liny9/aida/result/eval_0628/'

input_folder = '/nas/data/m1/lim22/aida2019/dryrun_3/0704/all_sources_aif_coref_lifu'
output_folder = '/nas/data/m1/lim22/aida2019/dryrun_3/0704/all_sources_aif_coref_entvec_lifu'
ent_vec_dir = '/data/m1/liny9/aida/result/dryrun3_0704/'

ent_vec_files = ['en_all/en.nam.tagged.hidden.txt', 'en_all/en.nom.5type.tagged.hidden.txt',
                 'en_all/en.nom.wv.tagged.hidden.txt', 'en_all/en.pro.tagged.hidden.txt',
                'ru_all/ru.nam.5type.tagged.hidden.txt', 'ru_all/ru.nam.wv.tagged.hidden.txt',
                'uk/uk.nam.5type.tagged.hidden.txt', 'uk/uk.nam.wv.tagged.hidden.txt']
# nam_5type > nam_wv > nom_5type > nom_wv > pro
# cs_file = '/data/m1/lim22/aida2019/dryrun_3/0610/entity_filler_fine_info.cs'

if os.path.exists(output_folder) is False:
    os.makedirs(output_folder)
# if os.path.exists(output_folder_json) is False:
#     os.makedirs(output_folder_json)

offset_vec = defaultdict(lambda : defaultdict(list))
vec_dim = 0
for ent_vec_file in ent_vec_files:
    ent_vec_type = ent_vec_file.split('/')[-1].replace('.tagged.hidden.txt', '')
    # print(ent_vec_type)
    for line in open(os.path.join(ent_vec_dir, ent_vec_file)):
        line = line.rstrip('\n')
        tabs = line.split('\t')
        offset = tabs[1]
        docid = offset.split(':')[0].replace('asr','').replace('ocrimg','').replace('ocrvideo','')
        start = int(offset.split(':')[1].split('-')[0])
        end = int(offset.split(':')[1].split('-')[1])
        vec = np.array(tabs[3].split(','), dtype='f')
        vec_dim = vec.size
        offset_vec[docid][ent_vec_type].append( (start, end, vec) )

# print(offset_vec['HC000Q7ZQ'])

prefix_AIDA = 'https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#'
AIDA = Namespace(prefix_AIDA)
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
LDC = Namespace('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#')

count_flag = 0
file_list = os.listdir(input_folder)
file_list_sorted = sorted(file_list)
count_doc = -1
for one_file in file_list_sorted:
    count_doc += 1
    if count_doc % total != num:
        continue

    ent_json_list = dict()
    print(one_file)
    if ".ttl" not in one_file:
        continue
    one_file_id = one_file.replace(".ttl", "")
    one_file_path = os.path.join(input_folder, one_file)
    output_file = os.path.join(output_folder, one_file)
    turtle_content = open(one_file_path).read()
    g = Graph().parse(data=turtle_content, format='ttl')

    # entities = []
    # for s, p, o in g:
    #     if 'type' in p and 'Entity' in o:
    #         entities.append(s)
    # print('entities: ', len(entities))
    entities = set()
    for entity in g.subjects(predicate=RDF.type, object=AIDA.Entity):
        for assertion in g.subjects(object=entity, predicate=RDF.subject):
            object_assrt = g.value(subject=assertion, predicate=RDF.object)
            predicate_assrt = g.value(subject=assertion, predicate=RDF.predicate)
            # only predicate ==`type`
            if predicate_assrt == RDF.type:
                parent_type = object_assrt.split('#')[-1].split('.')[0]
                if parent_type in ['PER', 'ORG', 'GPE', 'LOC', 'FAC', 'WEA', 'VEH', 'SID', 'CRM', 'BAL']:
                # if parent_type == 'VEH':
                    entities.add(entity)

    entity_offset_map = defaultdict(list)
    for s, p, o in g:
        if 'justifiedBy' in p:
            if s in entities:
                entity_offset_map[s].append(o)

    offset_info = dict()  # offset_dict[offset]['startOffset']=start, offset_dict[offset]['endOffsetInclusive']=end
    for s, p, o in g:
        p = p.toPython().split('#')[-1]
        # print(p)
        if 'startOffset' == p or 'endOffsetInclusive' == p or 'source' == p:
            if s not in offset_info:
                offset_info[s] = dict()
            offset_info[s][p] = o

    # print(offset_info)

    # average for entities:
    entity_vec = {}
    for entity in entity_offset_map:
        entity_vecs = []
        for ent_vec_file in ent_vec_files:
            ent_vec_type = ent_vec_file.split('/')[-1].replace('.tagged.hidden.txt', '')
            # print(ent_vec_type)
            for one_offset in entity_offset_map[entity]:
                # print(one_offset)
                if len(offset_info[one_offset]) != 3:
                    # print(offset_info[one_offset])
                    continue
                for one_offset_type in offset_info[one_offset]:
                    if 'startOffset' in one_offset_type:
                        start_offset = int(offset_info[one_offset][one_offset_type])
                    elif 'endOffsetInclusive' in one_offset_type:
                        end_offset = int(offset_info[one_offset][one_offset_type])
                    elif 'source' in one_offset_type :
                        docid = offset_info[one_offset][one_offset_type].toPython()
                search_key = "%s:%d-%d" % (docid, start_offset, end_offset)
                # print(offset_vec[docid], offset_vec['HC000Q7ZQ'])
                for (vec_start, vec_end, vec) in offset_vec[docid][ent_vec_type]:
                    # print(vec_start, vec_end, vec)
                    if vec_start >= start_offset and vec_end <= end_offset:
                        # print(search_key)
                        entity_vecs.append(vec)

            # entity_vec[entity] = np.average(entity_vecs, 0)
            if len(entity_vecs) > 0:
                entity_vec = np.average(entity_vecs, 0)
                # print(entity, entity_vec)
                system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/entity_representations")
                ent_vec_json_object = {'entity_vec_space': ent_vec_type,
                                       'entity_vec': ','.join(['%0.8f'%dim for dim in entity_vec])}
                ent_vec_json_content = json.dumps(ent_vec_json_object)
                # print(ent_vec_json_content)
                aifutils.mark_private_data(g, entity, ent_vec_json_content, system)
                # ent_json_list[entity] = ent_vec_json_content
                break

    g.serialize(destination=output_file, format='ttl')
    # json.dump(ent_json_list, open(os.path.join(output_folder_json, one_file_id + '.json'), 'w'), indent=4)

    # if len(entity_offset_map) != len(entities):
    #     print('entity_offset_map', len(entity_offset_map))
    #     print('entities', len(entities))

print("Now we have append the entity vectors")