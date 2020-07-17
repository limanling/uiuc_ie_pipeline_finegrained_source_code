import os
import re
import io
import itertools
import codecs
import tempfile
import numpy as np
import collections
from torch.autograd import Variable
from dnn_pytorch import LongTensor

try:
    import _pickle as cPickle
except ImportError:
    import cPickle

models_path = "./models"
eval_path = os.path.join(os.path.dirname(__file__), "./evaluation")
eval_temp = os.path.join(eval_path, "temp")
eval_script = os.path.join(eval_path, "conlleval")


def create_dico(item_list):
    """
    Create a dictionary of items from a list of list of items.
    """
    assert type(item_list) is list
    dico = {}
    for items in item_list:
        for item in items:
            if item not in dico:
                dico[item] = 1
            else:
                dico[item] += 1
    return dico


def create_mapping(dico):
    """
    Create a mapping (item to ID / ID to item) from a dictionary.
    Items are ordered by decreasing frequency.
    """
    sorted_items = sorted(dico.items(), key=lambda x: (-x[1], x[0]))
    id_to_item = {i: v[0] for i, v in enumerate(sorted_items)}
    item_to_id = {v: k for k, v in id_to_item.items()}
    return item_to_id, id_to_item


def zero_digits(s):
    """
    Replace every digit in a string by a zero.
    """
    return re.sub('\d', '0', s)


def iob2(tags):
    """
    Check that tags have a valid IOB format.
    Tags in IOB1 format are converted to IOB2.
    """
    for i, tag in enumerate(tags):
        if tag == 'O':
            continue
        split = tag.split('-')
        if len(split) != 2 or split[0] not in ['I', 'B']:
            return False
        if split[0] == 'B':
            continue
        elif i == 0 or tags[i - 1] == 'O':  # conversion IOB1 to IOB2
            tags[i] = 'B' + tag[1:]
        elif tags[i - 1][1:] == tag[1:]:
            continue
        else:  # conversion IOB1 to IOB2
            tags[i] = 'B' + tag[1:]
    return True


def iob_iobes(tags):
    """
    IOB -> IOBES
    """
    new_tags = []
    for i, tag in enumerate(tags):
        if tag == 'O':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'B':
            if i + 1 != len(tags) and \
                            tags[i + 1].split('-')[0] == 'I':
                new_tags.append(tag)
            else:
                new_tags.append(tag.replace('B-', 'S-'))
        elif tag.split('-')[0] == 'I':
            if i + 1 < len(tags) and \
                            tags[i + 1].split('-')[0] == 'I':
                new_tags.append(tag)
            else:
                new_tags.append(tag.replace('I-', 'E-'))
        else:
            raise Exception('Invalid IOB format!')
    return new_tags


def iobes_iob(tags):
    """
    IOBES -> IOB
    """
    new_tags = []
    for i, tag in enumerate(tags):
        if tag.split('-')[0] == 'B':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'I':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'S':
            new_tags.append(tag.replace('S-', 'B-'))
        elif tag.split('-')[0] == 'E':
            new_tags.append(tag.replace('E-', 'I-'))
        elif tag.split('-')[0] == 'O':
            new_tags.append(tag)
        else:
            raise Exception('Invalid format!')
    return new_tags


def insert_singletons(words, singletons, p=0.5):
    """
    Replace singletons by the unknown word with a probability p.
    """
    new_words = []
    for word in words:
        if word in singletons and np.random.uniform() < p:
            new_words.append(0)
        else:
            new_words.append(word)
    return new_words


def pad_word(inputs, seq_len):
    # get the max sequence length in the batch
    max_len = seq_len[0]

    padding = np.zeros_like([inputs[0][0]]).tolist()

    padded_inputs = []
    for item in inputs:
        padded_inputs.append(item + padding * (max_len - len(item)))

    return padded_inputs


def pad_chars(inputs):
    chained_chars = list(itertools.chain.from_iterable(inputs))

    char_index_mapping, chars = zip(
        *[item for item in sorted(
            enumerate(chained_chars), key=lambda x: len(x[1]), reverse=True
        )]
    )
    char_index_mapping = {v: i for i, v in enumerate(char_index_mapping)}

    char_len = [len(c) for c in chars]

    chars = pad_word(chars, char_len)

    # pad chars to length of 25 if max char len less than 25
    # char CNN layer requires at least 25 chars
    if len(chars[0]) < 25:
        chars = [c + [0]*(25-len(c)) for c in chars]

    return chars, char_index_mapping, char_len


def create_input(data, parameters, add_label=True):
    """
    Take sentence data and return an input for
    the training or the evaluation function.
    """
    # sort data by sequence length
    seq_index_mapping, data = zip(
        *[item for item in sorted(
            enumerate(data), key=lambda x: len(x[1]['words']), reverse=True
        )]
    )
    seq_index_mapping = {v: i for i, v in enumerate(seq_index_mapping)}

    inputs = collections.defaultdict(list)
    seq_len = []

    for d in data:
        words = d['words']
        seq_len.append(len(words))

#        chars = d['chars']

        if parameters['word_dim']:
            inputs['words'].append(words)
#        if parameters['char_dim']:
#            inputs['chars'].append(chars)
        if parameters['cap_dim']:
            caps = d['caps']
            inputs['caps'].append(caps)

        # boliang: add expectation features into input
#        if d['feats']:
#            inputs['feats'].append(d['feats'])

        if add_label:
            tags = d['tags']
            inputs['tags'].append(tags)

    char_index_mapping = []
    char_len = []
    for k, v in inputs.items():
        if k == 'chars':
            padded_chars, char_index_mapping, char_len = pad_chars(v)
            inputs[k] = padded_chars
        elif k in ['words', 'caps', 'feats', 'tags']:
            inputs[k] = pad_word(v, seq_len)

    # convert inputs and labels to Variable
    for k, v in inputs.items():
        inputs[k] = Variable(LongTensor(v))

    inputs['seq_index_mapping'] = seq_index_mapping
#    inputs['char_index_mapping'] = char_index_mapping
    inputs['seq_len'] = seq_len
#    inputs['char_len'] = char_len

    return inputs

#ann:
#def evaluate_trigger_tagger():
    
    
def evaluate_ner(parameters, preds, dataset, id_to_tag, eval_out_dir=None):
    """
    Evaluate current model using CoNLL script.
    """
    n_tags = len(id_to_tag)
    predictions = []
    count = np.zeros((n_tags, n_tags), dtype=np.int32)

    for d, p in zip(dataset, preds):
        assert len(d['words']) == len(p)
        p_tags = [id_to_tag[y_pred] for y_pred in p]
        r_tags = [id_to_tag[y_real] for y_real in d['tags']]
        if parameters['tag_scheme'] == 'iobes':
            p_tags = iobes_iob(p_tags)
            r_tags = iobes_iob(r_tags)
        for i, (y_pred, y_real) in enumerate(zip(p, d['tags'])):
            new_line = " ".join([d['str_words'][i]] + [r_tags[i], p_tags[i]])
            predictions.append(new_line)
            count[y_real, y_pred] += 1
        predictions.append("")

    # Write predictions to disk and run CoNLL script externally
    eval_id = np.random.randint(1000000, 2000000)
    if eval_out_dir:
        eval_temp = eval_out_dir
    eval_temp = tempfile.mkdtemp()
    output_path = os.path.join(eval_temp, "eval.%i.output" % eval_id)
    scores_path = os.path.join(eval_temp, "eval.%i.scores" % eval_id)
    with codecs.open(output_path, 'w', 'utf8') as f:
        f.write("\n".join(predictions))
    os.system("%s < %s > %s" % (eval_script, output_path, scores_path))
    print(output_path)
    # CoNLL evaluation results
    eval_lines = [l.rstrip() for l in codecs.open(scores_path, 'r', 'utf8')]
    for line in eval_lines:
        print(line)

    # Remove temp files
    # os.remove(output_path)
    # os.remove(scores_path)

    # Confusion matrix with accuracy for each tag
    # print(("{: >2}{: >7}{: >7}%s{: >9}" % ("{: >7}" * n_tags)).format(
    #     "ID", "NE", "Total",
    #     *([id_to_tag[i] for i in range(n_tags)] + ["Percent"])
    # ))
    # for i in range(n_tags):
    #     print(("{: >2}{: >7}{: >7}%s{: >9}" % ("{: >7}" * n_tags)).format(
    #         str(i), id_to_tag[i], str(count[i].sum()),
    #         *([count[i][j] for j in range(n_tags)] +
    #           ["%.3f" % (count[i][i] * 100. / max(1, count[i].sum()))])
    #     ))

    # Global accuracy
    print("%i/%i (%.5f%%)" % (
        count.trace(), count.sum(), 100. * count.trace() / max(1, count.sum())
    ))

    # F1 on all entities
    # print(eval_lines)

    # find all float numbers in string
    acc, precision, recall, f1 = re.findall("\d+\.\d+", eval_lines[1])

    return float(f1), float(acc), "\n".join(predictions)


########################################################################################################################
# temporal script below
#
def load_exp_feats(fp):
    bio_feats_fp = fp
    res = []
    for sent in io.open(bio_feats_fp, 'r', -1, 'utf-8').read().split('\n\n'):
        sent_feats = []
        for line in sent.splitlines():
            feats = line.split('\t')[1:]
            sent_feats.append(feats)
        res.append(sent_feats)

    return res


class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # If you want the output to be visible immediately

    def flush(self) :
        for f in self.files:
            f.flush()


if __name__ == "__main__":
    # dump train/dev/test exp feats for training
    train_exp_feats = load_exp_feats('train.bio.feats')
    dev_exp_feats = load_exp_feats('dev.bio.feats')
    test_exp_feats = load_exp_feats('test.bio.feats')

    with open('exp_feats.pkl', 'wb') as f:
        exp_feats = {
            'train_exp_feats': train_exp_feats,
            'dev_exp_feats': dev_exp_feats,
            'test_exp_feats': test_exp_feats,
        }
        cPickle.dump(exp_feats, f)

    # dump only test exp feats for testing
    test_exp_feats = load_exp_feats('test.bio.feats')
    cPickle.dump(test_exp_feats, open('test_exp_feats.pkl', 'wb'))


