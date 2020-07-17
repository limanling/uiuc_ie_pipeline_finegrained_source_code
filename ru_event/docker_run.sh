ltf="data/source/ru_all"
edl_bio="data/source/edl_results/ru.nam+nom.tagged.bio"
rsd="data/source/ru_all_rsd"
edl_cs="data/source/edl_results/ru.merged.cs"

docker run -v `pwd`:`pwd` -w `pwd` -i -t limanling/ru_event \
   /opt/conda/envs/ru_event/bin/python \
   ./ru_event/ru_event_backend.py \
   --ltf_folder_path ${ltf} \
   --input_edl_bio_file_path ${edl_bio} \
   --input_rsd_folder_path ${rsd} \
   --entity_cs_file_path ${edl_cs}

# /shared/nas/data/m1/whites5/AIDA/DependencyParse/data/ud-treebanks-v2.3