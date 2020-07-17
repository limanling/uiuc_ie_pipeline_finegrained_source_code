import os
import xml.etree.ElementTree as ET
import argparse

def parsing_doc_xml(xml_path):
    result_dict = dict()
    root = ET.parse(xml_path).getroot()
    for one_seg in root[0][0].findall('SEG'):
        for one_sentence in one_seg.findall('ORIGINAL_TEXT'):
            segment_id = one_seg.attrib['id']
            result_dict[segment_id] = one_sentence.text
    return result_dict

def parsing_aln_file(aln_path):
    result_list = list()
    f = open(aln_path)
    f.readline()
    for one_line in f:
        one_line = one_line.strip().lower()
        one_line_list = one_line.split('\t')
        result_list.append(one_line_list)
    f.close()
    return result_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('asr_ltf', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/source/ru_asr',
                        help='asr_ltf')
    parser.add_argument('asr_aln', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/raw_data/ru_asr',
                        help='asr_aln')
    parser.add_argument('asr_mapping_file_path', type=str,
                        default='/data/m1/lim22/aida2019/dryrun/source/asr_mapping/ru_asr_mapping',
                        help='asr_mapping_file_path')
    args = parser.parse_args()

    ltf_folder_path = args.asr_ltf
    aln_folder_path = args.asr_aln
    asr_mapping_file_path = args.asr_mapping_file_path

    if not os.path.exists(asr_mapping_file_path):
        os.makedirs(asr_mapping_file_path)

    for one_file in os.listdir(ltf_folder_path):
        if '.ltf.xml' not in one_file:
            continue
        to_write_list = list()
        one_file_id = one_file.replace('.ltf.xml', '')
        xml_file_path = os.path.join(ltf_folder_path, one_file)
        aln_file_path = os.path.join(aln_folder_path, '%s.aln' % one_file_id)
        xml_dict = parsing_doc_xml(xml_file_path)
        aln_list = parsing_aln_file(aln_file_path)
        count_flag = 0
        for one_seg_id in xml_dict:
            text_string = xml_dict[one_seg_id].lower()
            text_string_list = text_string.split(' ')
            start_offset = aln_list[count_flag][1]
            end_offset = aln_list[count_flag][2]
            for one_item in text_string_list:
                # print(aln_list[count_flag][0])
                aln_list[count_flag][0] = aln_list[count_flag][0].replace(one_item, '')
                # print(aln_list[count_flag][0])
                if len(aln_list[count_flag][0]) == 0:
                    count_flag += 1
            # print('aln_list[count_flag]', aln_list[count_flag])
            to_write_list.append("%s\t%s\t%s" % (one_seg_id, start_offset, end_offset))
        f_w = open(os.path.join(asr_mapping_file_path, '%s.map' % one_file_id), 'w')
        f_w.write('\n'.join(to_write_list))
        f_w.close()