import os
import shutil
from rdflib import Graph
import sys
import argparse


def load_doc_root_mapping(parent_child_tab_path, child_column_idx, parent_column_idx):
    doc_id_to_root_dict = dict()

    f = open(parent_child_tab_path)
    f.readline()

    for one_line in f:
        one_line = one_line.strip()
        one_line_list = one_line.split('\t')
        doc_id = one_line_list[child_column_idx]  #[3] # uid
        # doc_id = one_line_list[2] # child_uid
        root_id = one_line_list[parent_column_idx]  #[2] # parent_uid
        # root_id = one_line_list[7] # parent_uid
        doc_id_to_root_dict[doc_id] = root_id
    return doc_id_to_root_dict


def rename_to_root(input_private_folder, output_final_folder, doc_id_to_root_dict):
    for one_file in os.listdir(input_private_folder):
        if '.ttl' not in one_file:
            continue
        # print(one_file)
        file_id = one_file.replace('.ttl', '').replace('ocrimg', '').replace('ocrvideo', '').replace('asr', '')
        root_id = doc_id_to_root_dict[file_id]
        src_path = os.path.join(input_private_folder, one_file)
        dst_path = os.path.join(output_final_folder, '%s.ttl' % root_id)
        if os.path.exists(dst_path) is False:
            shutil.copy(src_path, dst_path)
        else:
            print('Repeated!')
            print(one_file)
            print(dst_path)
            turtle_content = open(dst_path).read()
            g = Graph().parse(data=turtle_content, format='ttl')
            source_turtle_content = open(src_path).read()
            g.parse(data=source_turtle_content, format='ttl')
            g.serialize(g.serialize(destination=dst_path, format='ttl'))

    print("Now we have changed the turtle file names for %s" % language_id)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--language_id', type=str,
                        help='Options: en | en_asr | en_ocr')
    # parser.add_argument('--data_source', type=str, default='',
    #                     help='Options: | _asr | _ocr | _ocr_video')
    parser.add_argument('--input_private_folder', type=str,
                        help='input directory (initial_private_data)')
    parser.add_argument('--output_folder', type=str,
                        help='output directory after renaming (final)')
    parser.add_argument('--parent_child_tab_path', type=str,
                        help='parent_children.tab')
    parser.add_argument('--child_column_idx', type=int, default=2,
                        help='the column_id of uid in parent_children.tab. Column_id starts from 0. ')
    parser.add_argument('--parent_column_idx', type=int, default=7,
                        help='the column_id of parent_uid in parent_children.tab. Column_id starts from 0. ')

    args = parser.parse_args()

    language_id = args.language_id
    input_private_folder = args.input_private_folder
    output_final_folder = args.output_folder
    parent_child_tab_path = args.parent_child_tab_path
    child_column_idx = args.child_column_idx
    parent_column_idx = args.parent_column_idx

    # language_id = sys.argv[1]
    # parent_child_tab_path = '/data/m1/AIDA_Data/LDC_raw_data/LDC2019E42_AIDA_Phase_1_Evaluation_Source_Data_V1.0/docs/parent_children.sorted.tab'
    # root_folder = '/data/m1/lim22/aida2019/LDC2019E42/0628/%s/' % language_id
    # root_folder = '/nas/data/m1/lim22/aida2019/TA1b_eval/E103_PT001/%s/' % language_id
    # parent_child_tab_path = '/data/m1/AIDA_Data/LDC_raw_data/LDC2018E62_AIDA_Month_9_Pilot_Eval_Corpus_V1.0/docs/parent_children.tab'
    # parent_child_tab_path = '/nas/data/m1/lim22/aida2019/dryrun_3/dryrun/docs/parent_children.tab'
    # root_folder = '/nas/data/m1/lim22/aida2019/i1/%s/' % language_id
    # input_private_folder = os.path.join(root_folder, 'initial_private_data')
    # output_final_folder = os.path.join(root_folder, 'final')

    if not os.path.exists(output_final_folder):
        os.makedirs(output_final_folder, exist_ok=True)
    else:
        shutil.rmtree(output_final_folder)
        os.makedirs(output_final_folder, exist_ok=True)

    if os.path.exists(parent_child_tab_path):
        doc_id_to_root_dict = load_doc_root_mapping(parent_child_tab_path, child_column_idx, parent_column_idx)
        rename_to_root(input_private_folder, output_final_folder, doc_id_to_root_dict)
        # print("Final result in RDF Format is in ", output_final_folder)
    else:
        shutil.copy(input_private_folder, output_final_folder)
        # print("Final result in RDF Format is in ", input_private_folder)
