import os
import shutil
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('asr_aln', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/raw_data/en_asr',
                        help='asr_aln')
    parser.add_argument('asr_rsd', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/source/en_asr_rsd',
                        help='asr_rsd')
    parser.add_argument('asr_rsd_file_list', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/en_asr_truecase_list',
                        help='asr_rsd_file_list')
    args = parser.parse_args()

    input_folder = args.asr_aln
    output_folder = args.asr_rsd
    file_list_path = args.asr_rsd_file_list

    if os.path.exists(output_folder) is True:
        shutil.rmtree(output_folder)
    os.makedirs(output_folder,exist_ok=True)

    f_list = open(file_list_path, 'w')
    for one_file in os.listdir(input_folder):
        if '.aln' not in one_file:
            continue
        one_file_path = os.path.join(input_folder, one_file)
        one_file_id = one_file.replace('.aln', '')
        one_file_output_path = os.path.join(output_folder, '%s.rsd.txt' % one_file_id)
        f_list.write('%s\n' % one_file_output_path)
        token_list = list()
        f_input = open(one_file_path)
        head_line = f_input.readline()
        for one_line in f_input:
            one_line = one_line.strip()
            one_line_list = one_line.split('\t')
            token_string = one_line_list[0]
            token_list.append(token_string)
        f_one_id = open(one_file_output_path, 'w')
        f_one_id.write(' '.join(token_list))
        f_one_id.close()
        f_input.close()
    f_list.close()