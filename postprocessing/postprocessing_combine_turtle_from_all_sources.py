import os
import shutil
from rdflib import Graph
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--root_folder', type=str,
                        help='root_folder')
    parser.add_argument('--final_dir_name', type=str,
                        help='final_dir_name')
    parser.add_argument('--output_folder', type=str,
                        help='output directory after merging')

    args = parser.parse_args()

    root_folder = args.root_folder  #'/data/m1/lim22/aida2019/dryrun_3/0704/' #package
    final_dir_name = args.final_dir_name  #'final'
    output_folder = args.output_folder  #os.path.join(root_folder, 'all_sources_aif_r2_tmp')
    language_id_list = ['en', 'ru', 'uk', 'en_asr', 'en_ocr', 'ru_ocr'] #['en_all_lifu', 'ru_all', 'uk']

    if os.path.exists(output_folder) is False:
        print("The folder does not exist, making one ...")
        os.makedirs(output_folder, exist_ok=True)
    else:
        print("The folder exists but we should purge it and remake one.")
        shutil.rmtree(output_folder)
        os.mkdir(output_folder)

    f_validator = open(os.path.join(root_folder, 'validator_candidates_list'), 'w')
    for one_language_id in language_id_list:
        input_folder = os.path.join(root_folder, one_language_id, final_dir_name)
        if not os.path.exists(input_folder):
            continue
        for one_file in os.listdir(input_folder):
            one_source_path = os.path.join(input_folder, one_file)
            one_dst_path = os.path.join(output_folder, one_file)
            if os.path.exists(one_dst_path) is False:
                shutil.copy(one_source_path, one_dst_path)
                print("Successfully copy %s" % one_file)
                f_validator.write('%s\n' % one_dst_path)
            else:
                print('Repeated root founded! Need merging')
                print('Merging %s' % one_dst_path)
                print('with %s' % one_source_path)
                turtle_content = open(one_dst_path).read()
                g = Graph().parse(data=turtle_content, format='ttl')
                source_turtle_content = open(one_source_path).read()
                g.parse(data=source_turtle_content, format='ttl')
                g.serialize(g.serialize(destination=one_dst_path, format='ttl'))
    f_validator.close()