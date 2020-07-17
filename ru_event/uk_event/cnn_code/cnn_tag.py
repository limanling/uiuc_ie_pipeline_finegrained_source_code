#Citation:
#Kim, Yoon. "Convolutional neural networks for sentence classification." arXiv preprint arXiv:1408.5882 (2014).
#https://github.com/dennybritz/cnn-text-classification-tf

import tensorflow as tf
import numpy as np
import os
import utils
from tensorflow.contrib import learn
import argparse

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    if x.ndim == 1:
        x = x.reshape((1, -1))
    max_x = np.max(x, axis=1).reshape((-1, 1))
    exp_x = np.exp(x - max_x)
    return exp_x / np.sum(exp_x, axis=1).reshape((-1, 1))

def predict(input_data, model_path, out_path):    

    # Eval Parameters
    tf.flags.DEFINE_integer("batch_size", 64, "Batch Size (default: 64)")
    tf.flags.DEFINE_string("checkpoint_dir", model_path, "Checkpoint directory from training run")
    
    # Misc Parameters
    tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
    tf.flags.DEFINE_boolean("log_device_placement", False, "Log placement of ops on devices")
    
    FLAGS = tf.flags.FLAGS
    FLAGS._parse_flags()
    
    
    datasets = None
    

    print("\nLoading...")
    
    datasets = utils.get_datasets_localdata(container_path=input_data)
    x_raw, y_test, target_labels, filenames = utils.load_data_labels(datasets)
    y_test = np.argmax(y_test, axis=1)
    
    # Map data into vocabulary
    vocab_path = os.path.join(FLAGS.checkpoint_dir, "..", "vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(x_raw)))
    
    print("\nPredicting...")
    
    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint(FLAGS.checkpoint_dir)
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(
          allow_soft_placement=FLAGS.allow_soft_placement,
          log_device_placement=FLAGS.log_device_placement)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
            saver.restore(sess, checkpoint_file)
    
            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]
    
            # Tensors we want to evaluate
            scores = graph.get_operation_by_name("output/scores").outputs[0]
    
            # Tensors we want to evaluate
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]
    
            # Generate batches for one epoch
            batches = utils.batch_iter(list(x_test), FLAGS.batch_size, 1, shuffle=False)
    
            # Collect the predictions here
            all_predictions = []
            all_probabilities = None
    
            for x_test_batch in batches:
                batch_predictions_scores = sess.run([predictions, scores], {input_x: x_test_batch, dropout_keep_prob: 1.0})
                all_predictions = np.concatenate([all_predictions, batch_predictions_scores[0]])
                probabilities = softmax(batch_predictions_scores[1])
                if all_probabilities is not None:
                    all_probabilities = np.concatenate([all_probabilities, probabilities])
                else:
                    all_probabilities = probabilities
    
    # Print accuracy if y_test is defined
    if y_test is not None:
        correct_predictions = float(sum(all_predictions == y_test))
    
    print("\nStoring Results...")
    raw_labels = []
    for prediction in all_predictions:
        raw_labels.append(target_labels[int(prediction)])
    confidences = []
    
    predictions_human_readable = np.column_stack((np.array(x_raw),
                                                  [label for label in raw_labels],
                                                  [name for name in filenames],
                                                  [ "{}".format(max(probability)) for probability in all_probabilities]))
    
    print("Saving results to {0}".format(out_path))
    with open(out_path, 'w') as f:
        constructor = []
        for line in predictions_human_readable:
            linetext = ""
            for element in line:
                linetext += str(element) + '\t'
            linetext = linetext.strip().replace('\x00','').replace('\n', ' ')
            constructor.append(linetext)
        f.write('\n'.join(constructor))


#####
def runner(model_path, out_folder_path, out_path):
    # default input data path
    input_data = os.path.join(out_folder_path, 'cnn_in')
    predict(input_data, model_path, out_path)

#####
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--input_data", default="intermediate_files/cnn_in/",
        help="location of cnn_in folders"
    )
    
    parser.add_argument(
        "--model_path", default='runs/uk_1535939547/checkpoints/',
        help="location of trained model"
    )
    
    parser.add_argument(
        "--out_path", default='intermediate_files/uk.tsv',
        help="location of output tsv file"
    )
    
    args = parser.parse_args()
    predict(args.input_data, args.model_path, args.out_path)     
