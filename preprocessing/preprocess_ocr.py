import os
import shutil
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('ocr_csv_file', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/raw_data/ocr/videos/vid.output/video.sampled.en.csv',
                        help='ocr_csv_file')
    parser.add_argument('ocr_rsd', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/source/en_ocr_rsd',
                        help='ocr_rsd')
    args = parser.parse_args()

    input_file = args.ocr_csv_file
    output_folder = args.ocr_rsd

    if os.path.exists(output_folder) is True:
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    output_dict = dict()

    for one_line in open(input_file):
        one_line = one_line.strip()
        one_line_list = one_line.split(",")
        if one_line_list[0] not in output_dict:
            output_dict[one_line_list[0].upper()] = list()
        output_dict[one_line_list[0].upper()].append(one_line_list[-1])

    for one_item in output_dict:
        f = open(os.path.join(output_folder, '%s.rsd.txt' % one_item), 'w')
        f.write("\n".join(output_dict[one_item]))
        f.close()