#!/usr/bin/env bash
CUDA_VISIBLE_DEVICES=2 python -u aida_depend.py \
--model_path "/data/m1/whites5/AIDA/DependencyParse/models/uk" \
--model_name "biaffine.pt" \
--gpu \
--punctuation '.' '``' "''" ':' ',' \
--decode mst \
train_phase \
--model_type FastLSTM \
--num_epochs 200 \
--batch_size 32 \
--hidden_size 512 \
--num_layers 3 \
--pos_dim 100 \
--char_dim 100 \
--num_filters 100 \
--arc_space 512 \
--type_space 128 \
--opt adam \
--learning_rate 0.001 \
--decay_rate 0.75 \
--epsilon 1e-4 \
--schedule 10 \
--gamma 0.0 \
--clip 5.0 \
--p_in 0.33 \
--p_rnn 0.33 0.33 \
--p_out 0.33 \
--unk_replace 0.5 \
--pos \
--objective cross_entropy \
--word_embedding sskip \
--word_path "/data/m1/whites5/AIDA/pretrained_embeddings/uk.ldc.emb.gz" \
--char_embedding "random" \
--train_data "/data/m1/whites5/AIDA/DependencyParse/data/ud-treebanks-v2.3/UD_Ukrainian-IU/uk_iu-ud-train.conllx" \
--dev_data "/data/m1/whites5/AIDA/DependencyParse/data/ud-treebanks-v2.3/UD_Ukrainian-IU/uk_iu-ud-dev.conllx" \
--test_data "/data/m1/whites5/AIDA/DependencyParse/data/ud-treebanks-v2.3/UD_Ukrainian-IU/uk_iu-ud-test.conllx"
