from rdflib import Graph, plugin, URIRef
from aida_interchange import aifutils

import os
import ujson as json
import traceback
import argparse
from collections import defaultdict
import numpy as np


def load_entity_vec(ent_vec_files, ent_vec_dir):
    offset_vec = defaultdict(lambda: defaultdict(list))
    # vec_dim = 0

    for ent_vec_file in ent_vec_files:
        ent_vec_type = ent_vec_file.split('/')[-1].replace('.tagged.hidden.txt', '')
        # print(ent_vec_type)
        for line in open(os.path.join(ent_vec_dir, ent_vec_file)):
            line = line.rstrip('\n')
            tabs = line.split('\t')
            if len(tabs) != 3:
                print(line)
            offset = tabs[1]
            docid = offset.split(':')[0] #.replace('asr', '').replace('ocrimg', '').replace('ocrvideo', '')
            start = int(offset.split(':')[1].split('-')[0])
            end = int(offset.split(':')[1].split('-')[1])
            vec = np.array(tabs[2].split(','), dtype='f')
            # vec_dim = vec.size
            offset_vec[docid][ent_vec_type].append((start, end, vec))
    return offset_vec


def add_filetype(g, one_unique_ke, filetype_str):
    system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/fileType")
    file_type_json_object = {'fileType': filetype_str}
    file_type_json_content = json.dumps(file_type_json_object)
    aifutils.mark_private_data(g, one_unique_ke, file_type_json_content, system)


def load_info(language_id, fine_grained_entity_type_path, freebase_link_mapping, lorelei_link_mapping,
              translation_path):
    fine_grained_entity_dict = json.load(open(fine_grained_entity_type_path))
    freebase_links = json.load(open(freebase_link_mapping))
    lorelei_links = json.load(open(lorelei_link_mapping))

    if 'en' not in language_id:
        translation_dict = json.load(open(translation_path))
    else:
        translation_dict = None

    return lorelei_links, freebase_links, fine_grained_entity_dict, translation_dict


def append_private_data(language_id, input_folder, lorelei_links, freebase_links, fine_grained_entity_dict,
                        translation_dict, offset_vec):

    count_flag = 0
    for one_file in os.listdir(input_folder):
        # print(one_file)
        if ".ttl" not in one_file:
            continue
        ent_json_list = dict()
        one_file_id = one_file.replace(".ttl", "")
        one_file_path = os.path.join(input_folder, one_file)
        output_file = os.path.join(output_folder, one_file)
        turtle_content = open(one_file_path).read()
        g = Graph().parse(data=turtle_content, format='ttl')

        # append EDL fine_grained_data
        # system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/EDL_FineGrained")
        # for p, s, o in g:
        #     if 'linkTarget' not in s:
        #         continue
        #     linking_info = o.split(':')[-1]
        #     if linking_info in fine_grained_entity_dict:
        #         fine_grained_json_object = fine_grained_entity_dict[linking_info]
        #         fine_grained_json_content = json.dumps(fine_grained_json_object)
        #         aifutils.mark_private_data(g, p, fine_grained_json_content, system)


        entities = []
        events = []
        args = []
        for s, p, o in g:
            # print(s, p, o)
            if 'type' in p and 'Entity' in o:
                add_filetype(g, s, language_id)
                entities.append(s)
            elif 'type' in p and 'Event' in o:
                add_filetype(g, s, language_id)
                events.append(s)
            elif 'type' in p and ('Statement' in o or 'Relation' in o):
                add_filetype(g, s, language_id)
                args.append(s)
        # print('entities: ', len(entities))
        # print('events: ', len(events))

        entity_offset_map = defaultdict(list)
        event_offset_map = defaultdict(list)
        for s, p, o in g:
            if 'justifiedBy' in p:
                if s in entities:
                    entity_offset_map[s].append(o)
                if s in events:
                    event_offset_map[s].append(o)
        # ###### old ########### change to one entity may have multiple offsets
        # entity_offset_map = {}
        # event_offset_map = {}
        # for s, p, o in g:
        #     if 'justifiedBy' in p:
        #         if s in entities:
        #             entity_offset_map[o] = s
        #         elif s in events:
        #             event_offset_map[o] = s

        offset_info = dict()  # offset_info[offset]['startOffset']=start, offset_info[offset]['endOffsetInclusive']=end
        for s, p, o in g:
            p = p.toPython().split('#')[-1]
            if 'startOffset' == p or 'endOffsetInclusive' == p or 'source' == p:
                if s not in offset_info:
                    offset_info[s] = dict()
                offset_info[s][p] = o

        # unique_events = []
        # for one_bnode in event_offset_map:
        #     if event_offset_map[one_bnode] in unique_events:
        #         continue
        #     if len(offset_info[one_bnode]) != 2:
        #         continue
        #     for one_offset_type in offset_info[one_bnode]:
        #         if 'startOffset' in one_offset_type:
        #             start_offset = int(offset_info[one_bnode][one_offset_type])
        #         elif 'endOffsetInclusive' in one_offset_type:
        #             end_offset = int(offset_info[one_bnode][one_offset_type])
        #     search_key = "%s:%d-%d" % (one_file_id, start_offset, end_offset)
        #
        #     # append event time
        #     try:
        #         time = time_map[search_key]
        #         time_norm = time_map_norm[search_key]
        #         system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/event_time")
        #         time_json_dict = {'time': time, 'time_norm': time_norm}
        #         time_json_content = json.dumps(time_json_dict)
        #         aifutils.mark_private_data(g, event_offset_map[one_bnode], time_json_content, system)
        #         unique_events.append(event_offset_map[one_bnode])
        #     except KeyError:
        #         pass
        #         # continue

        unique_entities = []
        # ###### old ########### change to one entity may have multiple offsets
        # for one_bnode in entity_offset_map:
        #     if len(offset_info[one_bnode]) != 2:
        #         continue
        #     for one_offset_type in offset_info[one_bnode]:
        #         if 'startOffset' in one_offset_type:
        #             start_offset = int(offset_info[one_bnode][one_offset_type])
        #         elif 'endOffsetInclusive' in one_offset_type:
        #             end_offset = int(offset_info[one_bnode][one_offset_type])
        #     search_key = "%s:%d-%d" % (one_file_id, start_offset, end_offset)
        for entity in entity_offset_map:
            entity_vecs = []
            for one_offset in entity_offset_map[entity]:
                if len(offset_info[one_offset]) != 3:
                    continue
                for one_offset_type in offset_info[one_offset]:
                    if 'startOffset' in one_offset_type:
                        start_offset = int(offset_info[one_offset][one_offset_type])
                    elif 'endOffsetInclusive' in one_offset_type:
                        end_offset = int(offset_info[one_offset][one_offset_type])
                    elif 'source' in one_offset_type:
                        docid = offset_info[one_offset][one_offset_type].toPython()
                search_key = "%s:%d-%d" % (docid, start_offset, end_offset)


                # append links
                if entity not in unique_entities:
                    # append Freebase linking result
                    try:
                        if search_key in freebase_links:
                            freebase_link = freebase_links[search_key]
                            system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/EDL_Freebase")
                            # freebase_json_dict = {'freebase_link': freebase_link}
                            # freebase_json_content = json.dumps(freebase_json_dict)
                            # aifutils.mark_private_data(g, one_offset, freebase_json_content, system)
                            freebase_json_content = json.dumps({'freebase_link': freebase_link})
                            aifutils.mark_private_data(g, entity, freebase_json_content, system)

                            # append EDL fine_grained_data
                            linking_info = sorted(freebase_link.items(), key=lambda x: x[1]['average_score'], reverse=True)[0][0]
                            # linking_info = freebase_link.split(':')[-1]
                            if linking_info in fine_grained_entity_dict:
                                fine_grained_json_object = fine_grained_entity_dict[linking_info]
                                fine_grained_json_content = json.dumps({'finegrained_type': fine_grained_json_object})
                                system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/EDL_FineGrained")
                                aifutils.mark_private_data(g, entity, fine_grained_json_content, system)

                        # append multiple confidence
                        if search_key in lorelei_links:
                            lorelei_link_dict = lorelei_links[search_key]
                            # print(lorelei_link_dict)
                            system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/EDL_LORELEI_maxPool")
                            p_link = URIRef('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#link')
                            p_link_target = URIRef('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#linkTarget')
                            for lorelei_link_ttl in g.objects(subject=entity, predicate=p_link):
                                link_target = str(g.value(subject=lorelei_link_ttl, predicate=p_link_target))#.split(':')[-1]
                                # print('link_target', link_target)
                                if search_key not in lorelei_links or link_target not in lorelei_links[search_key]: #???
                                    confidence = 0.001
                                else:
                                    confidence = lorelei_links[search_key][link_target]
                                # print('confidence', confidence)
                                aifutils.mark_confidence(g, lorelei_link_ttl, confidence, system)

                        # save entity
                        unique_entities.append(entity)
                    except KeyError as e:
                        traceback.print_exc()
                        pass



                # append translation (mention-level)
                if 'en' in language_id:
                    continue
                try:
                    translation_list = translation_dict[search_key]
                    system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/EDL_Translation")
                    translation_json_dict = {'translation': translation_list}
                    translation_json_content = json.dumps(translation_json_dict)
                    aifutils.mark_private_data(g, one_offset, translation_json_content, system)
                except KeyError:
                    pass
                    # continue


                # collect entity vectors (mention-level)
                for ent_vec_type in offset_vec[docid]:
                    for (vec_start, vec_end, vec) in offset_vec[docid][ent_vec_type]:
                        # print(vec_start, vec_end, vec)
                        if vec_start >= start_offset and vec_end <= end_offset:
                            # print(search_key)
                            entity_vecs.append(vec)
            # append entity vectors (mention-level)
            if len(entity_vecs) > 0:
                entity_vec = np.average(entity_vecs, 0)
                # print(entity, entity_vec)
                system = aifutils.make_system_with_uri(g, "http://www.rpi.edu/entity_representations")
                ent_vec_json_object = {'entity_vec_space': ent_vec_type,
                                       'entity_vec': ','.join(['%0.8f' % dim for dim in entity_vec])}
                ent_vec_json_content = json.dumps(ent_vec_json_object)
                # print(ent_vec_json_content)
                aifutils.mark_private_data(g, entity, ent_vec_json_content, system)
                # ent_json_list[entity] = ent_vec_json_content
                break


        g.serialize(destination=output_file, format='ttl')


    print("Now we have append the private data for %s" % language_id)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--language_id', type=str,
                        help='Options: en | en_asr | en_ocr')
    # parser.add_argument('--data_source', type=str, default='',
    #                     help='Options: | _asr | _ocr | _ocr_video')
    parser.add_argument('--initial_folder', type=str,
                        help='input directory (initial)')
    parser.add_argument('--output_folder', type=str,
                        help='output directory after adding private data (initial_private_data)')
    parser.add_argument('--fine_grained_entity_type_path', type=str,
                        help='%s.linking.freebase.fine.json')
    parser.add_argument('--freebase_link_mapping', type=str,
                        help='edl/freebase_private_data.json')
    parser.add_argument('--lorelei_link_mapping', type=str,
                        help='edl/lorelei_private_data.json')
    parser.add_argument('--translation_path', type=str, default='',
                        help='%s.linking.freebase.translations.json')
    parser.add_argument('--event_embedding_elmo', action='store_true',
                        help='append event embedding from ELMo')
    parser.add_argument('--event_embedding_from_file', action='store_true',
                        help='append event embedding from OneIE')
    parser.add_argument('--ent_vec_dir', type=str, default='',
                        help='ent_vec_dir')
    parser.add_argument('--ent_vec_files', nargs='+', type=str,
                        help='ent_vec_files')

    args = parser.parse_args()

    initial_folder = args.initial_folder
    output_folder = args.output_folder
    fine_grained_entity_type_path = args.fine_grained_entity_type_path
    freebase_link_mapping = args.freebase_link_mapping
    lorelei_link_mapping = args.lorelei_link_mapping
    translation_path = args.translation_path
    event_embedding_elmo = args.event_embedding_elmo
    ent_vec_dir=args.ent_vec_dir
    ent_vec_files=args.ent_vec_files

    # lang = args.lang
    # data_source = args.data_source
    # language_id = '%s%s' % (lang, data_source)

    # language_id = sys.argv[1]
    language_id = args.language_id
    lang = language_id.split('_')[0]

    # result_path = "/data/m1/lim22/aida2019/dryrun_3/0610/%s" % language_id
    #
    # # Change the input folder
    # initial_folder = os.path.join(result_path, "initial")
    # # Change the output folder
    # output_folder = os.path.join(result_path, "initial_private_data")

    # # Change the fine-grained folder
    # fine_grained_path = "/nas/data/m1/panx2/tmp/aida/eval/2019/%s/0610%s/" % (lang, language_id.replace(lang, ""))
    #
    # # English has no translation
    # translation_path = os.path.join(fine_grained_path, "%s.linking.freebase.translations.json" % lang)
    # # translation_path = "/nas/data/m1/panx2/tmp/aida/eval/2019/ru/0327_asr/ru.linking.freebase.translations.json"
    #
    # fine_grained_entity_type_path = os.path.join(fine_grained_path, "%s.linking.freebase.fine.json" % lang)
    # # freebase_links_mapping = os.path.join(fine_grained_path, "%s.linking.freebase.tab" % lang)
    # freebase_link_mapping = os.path.join(result_path, "edl/freebase_private_data.json")
    #
    # lorelei_link_mapping = os.path.join(result_path, 'edl/lorelei_private_data.json')
    #
    # # time_dict = os.path.join(result_path, "event/time_mapping.txt")

    if os.path.exists(output_folder) is False:
        os.mkdir(output_folder)

    lorelei_links, freebase_links, fine_grained_entity_dict, translation_dict = load_info(
        language_id, fine_grained_entity_type_path, freebase_link_mapping,
        lorelei_link_mapping, translation_path)

    offset_vec = load_entity_vec(ent_vec_files, ent_vec_dir)

    append_private_data(language_id, initial_folder, lorelei_links, freebase_links,
                        fine_grained_entity_dict, translation_dict, offset_vec)

