import argparse
import time
import torch

from dnn_pytorch.seq_labeling.nn import SeqLabeling
from dnn_pytorch.seq_labeling.utils import create_input, iobes_iob
from dnn_pytorch.seq_labeling.loader import prepare_dataset_, load_sentences

#####
def run_tagger(model, input_file, output_file, batch_size, gpu):
    print('loading model from:', model)
    if gpu:
        state = torch.load(model)
    else:
        state = torch.load(model, map_location=lambda storage, loc: storage)

    parameters = state['parameters']
    mappings = state['mappings']

    # Load reverse mappings
    word_to_id, tag_to_id = [
        {v: k for k, v in x.items()}
        for x in [mappings['id_to_word'],  mappings['id_to_tag']]
        ]

    # eval sentences
    eval_sentences = load_sentences(
        input_file,
        parameters['lower'],
        parameters['zeros']
    )

    eval_dataset = prepare_dataset_(
        eval_sentences, 
        word_to_id,  tag_to_id, parameters['lower'],
        is_train=False
    )

    print("%i sentences in eval set." % len(eval_dataset))

    # initialize model
    model = SeqLabeling(parameters)
    model.load_state_dict(state['state_dict'])
    model.train(False)

    since = time.time()
    batch_size = batch_size
    f_output = open(output_file.replace('.bio','_intermediate.bio'), 'w')

    # Iterate over data.
    print('tagging...')
    for i in range(0, len(eval_dataset), batch_size):
        inputs = create_input(eval_dataset[i:i+batch_size], parameters, add_label=False)

        # forward
        outputs, loss = model.forward(inputs)

        seq_index_mapping = inputs['seq_index_mapping']
        seq_len = inputs['seq_len']
        if parameters['crf']:
            preds = [outputs[seq_index_mapping[j]].data
                     for j in range(len(outputs))]
        else:
            _confidences, _preds = torch.max(outputs.data, 2)

            preds = [
                _preds[seq_index_mapping[j]][:seq_len[seq_index_mapping[j]]]
                for j in range(len(seq_index_mapping))
                ]
            confidences = [
                    _confidences[seq_index_mapping[j]][:seq_len[seq_index_mapping[j]]]
                    for j in range(len(seq_index_mapping))
                    ]
    #        print(confidences)
            
        for j, pred in enumerate(preds):
            pred = [mappings['id_to_tag'][p] for p in pred]
            # Output tags in the IOB2 format
            if parameters['tag_scheme'] == 'iobes':
                pred = iobes_iob(pred)
            # Write tags
            assert len(pred) == len(eval_sentences[i+j])

            f_output.write('%s\n\n' % '\n'.join('%s%s%s' % (' '.join(w), ' ', ' '.join([z, str(q)]))
                                                for w, z, q in zip(eval_sentences[i+j],
                                                                pred, confidences[j])))
            #progress so far?
            if (i + j + 1) % 2000 == 0:
                print(i+j+1, '/', len(preds)+len(eval_dataset))

    end = time.time()  # epoch end time
    print('time elapssed: %f seconds' % round(
        (end - since), 2))
    f_output.close()


    print('\n retrieving offset information \n')
    with open(output_file.replace('.bio','_intermediate.bio'), 'r', encoding = 'utf-8') as mentfile,\
        open(input_file.replace('.bio','_offset.bio'), 'r', encoding = 'utf-8') as offsetfile:
                
        mentbios = mentfile.read().split('\n')
        offsetbios = offsetfile.read()
        for loopvar in range(25):
            offsetbios = offsetbios.replace('\n\n\n', '\n\n').replace('\n\n\n', '\n\n')
        offsetbios = offsetbios.split('\n')
            
        newfile = []
        for i, ment in enumerate(mentbios):
            newline = ""
            if ment.strip():
                newline = ' '.join([ ment.strip().split(' ')[0] , offsetbios[i].strip().split(' ')[1] , ment.strip().split(' ')[2] , ment.strip().split(' ')[3]] )
                newfile.append(newline)
                if len(ment.strip().split(' ')[0]) != len(offsetbios[i].strip().split(' ')[0]): # error checking for alignment when adding back the offset information
                    print('ERROR:', ment.strip().split(' ')[0])
                    print(offsetbios[i].strip().split(' ')[0])
                    print('')
            else:
                newfile.append('')
        with open(output_file, 'w', encoding = 'utf-8') as outfile:
                outfile.write('\n'.join(newfile))

#####
def runner(model, input_file, output_file, batch_size, gpu):
    run_tagger(model, input_file, output_file, batch_size, gpu)

#####
if __name__ == "__main__":

    # Read parameters from command line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", default="",
        help="Model location"
    )
    parser.add_argument(
        "--input", default="",
        help="Input bio file location"
    )
    parser.add_argument(
        "--output", default="",
        help="Output bio file location"
    )
    parser.add_argument(
        "--batch_size", default="50",
        type=int, help="batch size"
    )
    parser.add_argument(
        "--gpu", default="0",
        type=int, help="default is 0. set 1 to use gpu."
    )
    args = parser.parse_args()

    run_tagger(args.model, args.input, args.output, args.batch_size, args.gpu)
