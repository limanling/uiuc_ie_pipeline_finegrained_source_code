import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('params_file', type=str, help='params_file')
    parser.add_argument('input_cs', type=str, help='input cold start')
    parser.add_argument('output_ttl', default=str, help='output_ttl')
    args = parser.parse_args()

    with open(args.params_file, 'w') as writer:
        writer.write("inputKBFile: /aida-tools-master/sample_params/m18-eval/%s\n" % args.input_cs)
        writer.write("outputAIFDirectory: /aida-tools-master/sample_params/m18-eval/%s\n" % args.output_ttl)
        writer.write("baseURI: http://www.isi.edu/gaia\n")
        writer.write("systemURI: http://www.rpi.edu\n")
        writer.write("mode: SHATTER\n")
        writer.write("includeDebugPrefLabels: true\n")
        writer.write("entityOntology: /AIDA-Interchange-Format-master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntology\n")
        writer.write("relationOntology: /AIDA-Interchange-Format-master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntology\n")
        writer.write("eventOntology: /AIDA-Interchange-Format-master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntology\n")

    # echo "inputKBFile: /aida-tools-master/sample_params/m18-eval/"${merged_cs_link} > ${data_root}/converter.param
    # echo "outputAIFDirectory: /aida-tools-master/sample_params/m18-eval/"${ttl_initial} >> ${data_root}/converter.param
    # echo "baseURI: http://www.isi.edu/gaia" >> ${data_root}/converter.param
    # echo "systemURI: http://www.rpi.edu" >> ${data_root}/converter.param
    # echo "mode: SHATTER" >> ${data_root}/converter.param
    # echo "includeDebugPrefLabels: true" >> ${data_root}/converter.param
    # echo "entityOntology: /AIDA-Interchange-Format-master/src/main/resources/com/ncc/aif/ontologies/LDCOntology" >> ${data_root}/converter.param
    # echo "relationOntology: /AIDA-Interchange-Format-master/src/main/resources/com/ncc/aif/ontologies/LDCOntology" >> ${data_root}/converter.param
    # echo "eventOntology: /AIDA-Interchange-Format-master/src/main/resources/com/ncc/aif/ontologies/LDCOntology" >> ${data_root}/converter.param
