from collections import defaultdict
import os
from aida_interchange import aifutils
from rdflib import Graph, Namespace, URIRef, term
# import ujson as json
import json
import argparse

AIDA = Namespace('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
LDC = Namespace('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#')


def parse_offset_str(offset_str):
    docid = offset_str[:offset_str.find(':')]
    start = int(offset_str[offset_str.find(':') + 1:offset_str.find('-')])
    end = int(offset_str[offset_str.find('-') + 1:])
    return docid, start, end


def load_parent_child(parent_child_tab_path, child_column_idx, parent_column_idx):
    root2child = defaultdict(set)
    f = open(parent_child_tab_path)
    f.readline()
    for one_line in f:
        one_line = one_line.strip()
        one_line_list = one_line.split('\t')
        # doc_id = one_line_list[3] # child_uid
        doc_id = one_line_list[child_column_idx] # child_uid
        # root_id = one_line_list[2] # parent_uid
        root_id = one_line_list[parent_column_idx] # parent_uid
        root2child[root_id].add(doc_id)
    return root2child


def load_relation_result(relation_add_files):
    doc_rel = defaultdict(set)
    rel_info = defaultdict(lambda : defaultdict())
    rel_args = defaultdict(lambda : defaultdict())
    for lang in relation_add_files:
        relation_add_file = relation_add_files[lang]
        for line in open(relation_add_file):
            line = line.rstrip('\n')
            tabs = line.split('\t')

            rel_id = lang.upper()+'_'+tabs[0][1:]
            if tabs[1] == 'type':
                rel_info[rel_id]['type'] = tabs[2].split('#')[-1]
            elif 'canonical_mention' in tabs[1]:
                offset = tabs[3]
                docid, start, end = parse_offset_str(offset)
                doc_rel[docid].add(rel_id)
                rel_info[rel_id]['confidence'] = float(tabs[4])
                rel_info[rel_id]['mention'] = offset.replace("asr", "").replace("ocrimg", "").replace("ocrvideo", "")
                if "asr" in offset:
                    rel_info[rel_id]['filetype'] = lang+'_asr'
                elif "ocrvideo" in offset:
                    rel_info[rel_id]['filetype'] = lang + '_ocr_video'
                elif "ocrimg" in offset:
                    rel_info[rel_id]['filetype'] = lang + '_ocr_img'
                else:
                    rel_info[rel_id]['filetype'] = lang
            elif 'mention' not in tabs[1]:
                role = tabs[1].split('#')[-1]
                ent_offset = tabs[3]
                rel_args[rel_id][role] = ent_offset.replace("asr", "").replace("ocrimg", "").replace("ocrvideo", "")

    return doc_rel, rel_info, rel_args


def add_filetype(g, one_unique_ke, filetype_str):
    system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/fileType")
    file_type_json_object = {'fileType': filetype_str}
    file_type_json_content = json.dumps(file_type_json_object)
    aifutils.mark_private_data(g, one_unique_ke, file_type_json_content, system)


def add_relation(input_ttl_folder, output_ttl_folder, root2child,
                 doc_rel, rel_info, rel_args):
    for one_file in os.listdir(input_ttl_folder):
    # file_list_sorted = sorted(os.listdir(input_ttl_folder))
    # count = -1
    # for one_file in file_list_sorted:
    #     count += 1
        # if count % total != num:
        #     continue

        # print(one_file)
        if not one_file.endswith(".ttl"):
            continue
        one_file_id = one_file.replace(".ttl", "")
        one_file_path = os.path.join(input_ttl_folder, one_file)
        turtle_content = open(one_file_path).read()

        g = Graph().parse(data=turtle_content, format='ttl')

        entities = set()
        for entity in g.subjects(predicate=RDF.type, object=AIDA.Entity):
            for assertion in g.subjects(object=entity, predicate=RDF.subject):
                object_assrt = g.value(subject=assertion, predicate=RDF.object)
                predicate_assrt = g.value(subject=assertion, predicate=RDF.predicate)
                # only predicate ==`type`
                if predicate_assrt == RDF.type:
                    parent_type = object_assrt.split('#')[-1].split('.')[0]
                    if parent_type in ['PER', 'ORG', 'GPE', 'LOC', 'FAC', 'WEA', 'VEH', 'SID', 'CRM', 'BAL']:
                        entities.add(entity)
        for event in g.subjects(predicate=RDF.type, object=AIDA.Event):
            entities.add(event)
        # for s, p, o in g:
        #     # print(s, p, o)
        #     if 'type' in p and ('Entity' in o or 'Event' in o):
        #         entities.append(s)

        entity_offset_map = {}  # offset -> entity
        # event_offset_map = {}
        for s, p, o in g:
            if 'justifiedBy' in p:
                if s in entities:
                    entity_offset_map[o] = s
                # elif s in events:
                #     event_offset_map[o] = s

        offset_dict = dict()
        offset_filetype = dict()
        for s, p, o in g:
            p = p.toPython().split('#')[-1]
            if 'startOffset' == p or 'endOffsetInclusive' == p or 'source' == p:
                if s not in offset_dict:
                    offset_dict[s] = dict()
                    offset_dict[s][p] = o
                else:
                    offset_dict[s][p] = o

        offset_str2entity = dict()
        for one_bnode in entity_offset_map:
            if len(offset_dict[one_bnode]) != 3:
                continue
            for one_offset_type in offset_dict[one_bnode]:
                if 'startOffset' in one_offset_type:
                    start_offset = int(offset_dict[one_bnode][one_offset_type])
                elif 'endOffsetInclusive' in one_offset_type:
                    end_offset = int(offset_dict[one_bnode][one_offset_type])
                elif 'source' in one_offset_type:
                    docid = offset_dict[one_bnode][one_offset_type].toPython()
            search_key = "%s:%d-%d" % (docid, start_offset, end_offset)
            offset_str2entity[search_key] = entity_offset_map[one_bnode]

        # print(offset_str2entity)

        system = aifutils.make_system_with_uri(g, "http://www.columbia.edu/Columbia_Sentiment")
        for doc_id in root2child[one_file_id]:
            # print(doc_id)
            for rel_id in doc_rel[doc_id]:
                # print('add relation ', rel_id)
                should_delete = False
                for role in rel_args[rel_id]:
                    role_offset = rel_args[rel_id][role]
                    if role_offset not in offset_str2entity:
                        print('[ERROR] No Knowledge element ', role_offset)
                        should_delete = True
                if should_delete:
                    continue

                relation_uri = "http://www.columbia.edu/ColumbiaSentiment/%s" % rel_id
                relation = aifutils.make_relation(g, relation_uri, system)

                confidence = rel_info[rel_id]['confidence']
                relation_type = LDC[rel_info[rel_id]['type']]
                docid, start, end = parse_offset_str(rel_info[rel_id]['mention'])

                type_assertion_uri = "http://www.columbia.edu/ColumbiaSentimentType/%s" % rel_id
                type_asser = aifutils.mark_type(g, type_assertion_uri, relation, relation_type, system, confidence)
                informative_uri = "http://www.columbia.edu/ColumbiaSentimentInformative/%s" % rel_id
                informative_justification = aifutils.mark_text_justification(g, [relation, type_asser], docid, start,
                                                                             end, system, confidence,
                                                                             informative_uri)
                add_filetype(g, informative_justification, rel_info[rel_id]['filetype'])
                aifutils.mark_informative_justification(g, relation, informative_justification)

                for role in rel_args[rel_id]:
                    subject_role = LDC[role]
                    role_offset = rel_args[rel_id][role]
                    role_docid, role_start, role_end = parse_offset_str(role_offset)
                    subject_resource = offset_str2entity[role_offset]
                    role_asser = aifutils.mark_as_argument(g, relation, subject_role, subject_resource, system, confidence)
                    role_justification = aifutils.mark_text_justification(g, [role_asser], role_docid, role_start,
                                                                          role_end, system, confidence,
                                                                          uri_ref=None)

                    add_filetype(g, role_justification, rel_info[rel_id]['filetype'])

    # relation = aifutils.make_relation_in_event_form(g, relation_uri, relation_type, subject_role, subject_resource, object_role,
    #                                     object_resource, type_assertion_uri, system, confidence)

        g.serialize(destination=os.path.join(output_ttl_folder, one_file), format='ttl')

    print("Added sentiment relations from CU, output in", output_ttl_folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument("--relation_cs_files", nargs="+",
    #                        help="List of paths to input CS files.", required=True)
    parser.add_argument("--relation_cs_files", type=json.loads,
                        help="a json indicating the language_id and the relation files", required=True)
    parser.add_argument("--input_ttl_folder", help="input_ttl_folder", required=True)
    parser.add_argument("--output_ttl_folder", help="output_ttl_folder", required=True)
    parser.add_argument("--parent_child_tab_path", help="parent_child_tab_path", required=True)
    parser.add_argument('--child_column_idx', type=int,
                        help='the column_id of uid in parent_children.tab. Column_id starts from 0. ')
    parser.add_argument('--parent_column_idx', type=int,
                        help='the column_id of parent_uid in parent_children.tab. Column_id starts from 0. ')
    args = parser.parse_args()

    input_ttl_folder = args.input_ttl_folder
    output_ttl_folder = args.output_ttl_folder
    parent_child_tab_path = args.parent_child_tab_path
    child_column_idx = args.child_column_idx
    parent_column_idx = args.parent_column_idx
    relation_cs_files = args.relation_cs_files

    # relation_add_files = {
    #     'en': '/data/m1/lim22/aida2019/dryrun_3/0704/sponsor_relation/en.r2.multi_sent.sponsor_assignblame.cs',
    #     'ru': '/data/m1/lim22/aida2019/dryrun_3/0704/sponsor_relation/ru.multi_sent.sponsor_assignblame.cs',
    #     'uk': '/data/m1/lim22/aida2019/dryrun_3/0704/sponsor_relation/uk.multi_sent.sponsor_assignblame.cs'
    # }

    # parent_child_tab_path = '/nas/data/m1/lim22/aida2019/dryrun_3/dryrun/docs/parent_children.tab'
    #
    # input_ttl_folder = '/data/m1/lim22/aida2019/dryrun_3/0704/merged_ttl_D3_GAIA_2/merged_ttl_D3_GAIA_2_final_coreferall'
    # output_ttl_folder = '/data/m1/lim22/aida2019/dryrun_3/0704/merged_ttl_D3_GAIA_2/merged_ttl_D3_GAIA_2_final_coreferall_rel'

    if not os.path.exists(output_ttl_folder):
        os.makedirs(output_ttl_folder)
    print(output_ttl_folder)

    root2child = load_parent_child(parent_child_tab_path, child_column_idx, parent_column_idx)
    doc_rel, rel_info, rel_args = load_relation_result(relation_cs_files)
    add_relation(input_ttl_folder, output_ttl_folder, root2child,
                 doc_rel, rel_info, rel_args)