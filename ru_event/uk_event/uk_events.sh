#clean up the directory structure and intermediate files before starting
python clean_up.py

#Construct bio files (ru_all.bio and ru_all_offset.bio) from the ltf files and store it in intermediate results folder for later use 
python ltf_to_bio.py --ltf_folder_path data/source/uk --out_file_path intermediate_files

#Run trigger extraction with the bio files from previous step
python trigger_code/dnn_pytorch/tag.py --model trigger_code/dnn_pytorch/best_model.pth.tar --input intermediate_files/uk_all.bio --output intermediate_files/uk_all_triggers_offset.bio --batch_size 50 --gpu 0

#use the output file from prev step, and bio file from EDL results, to create a merged bio for candidate arguments
python combine_ment_arg_new.py --input_trigger_offset_file intermediate_files/uk_all_triggers_offset.bio --input_edl_bio_file data/source/edl_results/uk.nam+nom.tagged.bio --output_file intermediate_files/uk_all_merged.bio

#use rsd files, the merged bio from prev step, and generate input to the argument extraction model
python cnn_input_dryrun.py --input_rsd_folder data/source/uk_rsd --input_merged_bio intermediate_files/uk_all_merged.bio

#Argument extraction
python cnn_code/cnn_tag.py --model_path cnn_code/runs/uk_1535939547/checkpoints/ --out_path intermediate_files/uk_all.tsv

#Apply post processing rules and convert to CS format
python output_formatter_new_v5_singlecs_m18.py --rsdpath data/source/uk_rsd/ --entity_cs_path data/source/edl_results/uk.merged.cs --cspath results/uk_all.cs --trig_offset_file intermediate_files/uk_all_triggers_offset.bio --cnn_out_file intermediate_files/uk_all.tsv