from langdetect import detect, DetectorFactory
import shutil
import os
import argparse
import io


def detect_lang(rsd_input_folder, ltf_input_folder, output_folder):
    DetectorFactory.seed = 0

    # if os.path.exists(output_folder) is True:
    #     shutil.rmtree(output_folder)
    #
    # os.mkdir(output_folder)

    # rsd_input_folder = os.path.join(input_folder, 'rsd')
    # ltf_input_folder = os.path.join(input_folder, 'ltf')
    for one_file in os.listdir(rsd_input_folder):
        if not one_file.endswith('.rsd.txt'):
            continue
        one_file_id = one_file.replace('.rsd.txt', '')
        one_rsd_file_path = os.path.join(rsd_input_folder, one_file)
        one_ltf_file_path = os.path.join(ltf_input_folder, '%s.ltf.xml' % one_file_id)
        one_file_content = io.open(one_rsd_file_path, mode='r', encoding='utf-8').read()
        candidate_language_id = detect(one_file_content)
        language_folder_ltf = os.path.join(output_folder, candidate_language_id, 'ltf')
        if os.path.exists(language_folder_ltf) is False:
            os.makedirs(language_folder_ltf, exist_ok=True)
        shutil.copy(one_ltf_file_path, language_folder_ltf)
        language_folder_rsd = os.path.join(output_folder, candidate_language_id, 'rsd')
        if os.path.exists(language_folder_rsd) is False:
            os.makedirs(language_folder_rsd, exist_ok=True)
        shutil.copy(one_rsd_file_path, language_folder_rsd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rsd_input_folder', type=str,
                        help='input directory of all rsd files')
    parser.add_argument('ltf_input_folder', type=str,
                        help='input directory of all ltf files')
    parser.add_argument('output_folder', type=str,
                        help='output directory divided by languages')
    args = parser.parse_args()

    rsd_input_folder = args.rsd_input_folder
    ltf_input_folder = args.ltf_input_folder
    output_folder = args.output_folder
    # input_folder = '/data/m1/AIDA_Data/LDC_raw_data/LDC2018E01_AIDA_Seedling_Corpus_V2.0/data/'
    # output_folder = '/data/m1/zhangt13/aida2018/1118/E01/source'

    # input_folder = '/data/m1/lim22/aida2019/dryrun_3/dryrun/data'
    # output_folder = '/data/m1/lim22/aida2019/dryrun_3/source'
    # input_folder = '/data/m1/AIDA_Data/LDC_raw_data/LDC2019E42_AIDA_Phase_1_Evaluation_Source_Data_V1.0/data'
    # rsd_input_folder = os.path.join(input_folder, 'rsd')
    # ltf_input_folder = os.path.join(input_folder, 'ltf','ltf')
    # output_folder = '/data/m1/lim22/aida2019/LDC2019E42/source'

    detect_lang(rsd_input_folder, ltf_input_folder, output_folder)
