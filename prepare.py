import argparse
import os
import time
import pickle
import codecs
import numpy as np
import pandas as pd
from collections import Counter
from nltk.tokenize import TweetTokenizer
import multiprocessing as mp


def main():
    parser = argparse.ArgumentParser(description='TextLevelGNN data preprocess script')
    parser.add_argument('--dataset', type=str, default='R8', choices=['mr', 'ohsumed', 'R8', 'R52'],
                        help='name of dataset used')
    parser.add_argument('--path_data', type=str, default='./data/',
                        help='path of the data corpus')
    parser.add_argument('--max_len_text', type=int, default=100,
                        help='maximum length of text')
    parser.add_argument('--n_word_min', type=int, default=2,
                        help='minimum word counts')

    parser.add_argument('--preserve_case', type=bool, default=False,
                        help='preserve words case')
    parser.add_argument('--pad_num', type=bool, default=True,
                        help='pad all numbers to a same <num>')

    parser.add_argument('--pretrained', type=bool, default=True,
                        help='use _pretrained GloVe_300d')
    parser.add_argument('--d_pretrained', type=int, default=300,
                        help='pretrained embedding dimension')
    parser.add_argument('--path_pretrained', type=str, default='./data/glove.6B.300d.txt',
                        help='path of pretrained GloVe embeddings')
    parser.add_argument('--seed', type=int, default=1111,
                        help='random seed')

    args = parser.parse_args()
    if args.dataset == 'ohsumed':
        args.dataset = 'ohsumed_single_23'
        args.n_word_min = 3

    if not os.path.exists(args.path_data + args.dataset):
        raise FileNotFoundError('Dataset "{data}" raw corpus file not found.'.format(data=args.dataset))

    # data preprocess
    print('\n[info] Dataset:', args.dataset)
    time_start = time.time()

    tr_data, te_data, tr_gt, te_gt = read_corpus(args)
    tr_tokens, te_tokens, tr_gt, te_gt = tokenize(args, tr_data, te_data, tr_gt, te_gt)

    x, y, word2idx = extract_feature(tr_processed, te_processed, n_word_min=args.n_word_min)

    embeds = get_embedding(args, word2idx)

    # save processed data
    n_train = df_data.subset.value_counts()['train']
    mappings = {
        'tr_data': x[:n_train],
        'tr_gt': y[:n_train],
        'te_data': x[n_train:],
        'te_gt': y[n_train:],
        'word2idx': word2idx,
        'embeds': embeds,
        'args': args
    }
    with open(args.path_data + args.dataset + '.pkl', 'wb') as f:
        pickle.dump(mappings, f)

    print('\n[info] Time consumed: {:.2f}s'.format(time.time() - time_start))


def read_corpus(args):
    """ Export data from corpus file """

    path_data, dataset = args.path_data + args.dataset, args.dataset
    tr_data, te_data, tr_gt, te_gt = [], [], [], []

    # R20
    if dataset == 'R8' or dataset == 'R52':
        with open(os.path.join(path_data, 'train.txt')) as f:
            lines = f.readlines()

        for line in lines:
            label, text = line.strip().split('\t')
            tr_data.append([text])
            tr_gt.append([label])

        with open(os.path.join(path_data, 'test.txt')) as f:
            lines = f.readlines()
        for line in lines:
            label, text = line.strip().split('\t')
            te_data.append([text])
            te_gt.append([label])

    # ohsumed_single_23
    elif dataset == 'ohsumed_single_23':

        path_data_subset = os.path.join(path_data, 'training')
        for label in os.listdir(path_data_subset):
            for doc in os.listdir(os.path.join(path_data_subset, label)):
                with open(os.path.join(path_data_subset, label, doc)) as f:
                    lines = f.readlines()
                text = " ".join([line.strip() for line in lines])
                tr_data.append([text])
                tr_gt.append([label])

        path_data_subset = os.path.join(path_data, 'test')
        for label in os.listdir(path_data_subset):
            for doc in os.listdir(os.path.join(path_data_subset, label)):
                with open(os.path.join(path_data_subset, label, doc)) as f:
                    lines = f.readlines()
                text = " ".join([line.strip() for line in lines])
                te_data.append([text])
                te_gt.append([label])

    # movie review
    elif dataset == 'mr':

        text_data_path = os.path.join(path_data, 'text_train.txt')
        with open(text_data_path, 'rb') as f:
            text_lines = f.readlines()
        label_data_path = os.path.join(path_data, 'label_train.txt')
        with open(label_data_path, 'rb') as f:
            label_lines = f.readlines()
        for (text, label) in zip(text_lines, label_lines):
            tr_data += [str(text.strip())]
            tr_gt += [str(label.strip())]

        text_data_path = os.path.join(path_data, 'text_test.txt')
        with open(text_data_path, 'rb') as f:
            text_lines = f.readlines()
        label_data_path = os.path.join(path_data, 'label_test.txt')
        with open(label_data_path, 'rb') as f:
            label_lines = f.readlines()
        for (text, label) in zip(text_lines, label_lines):
            te_data += [str(text.strip())]
            te_gt += [str(label.strip())]

    else:
        raise FileNotFoundError('Dataset not supported.')

    return tr_data, te_data, tr_gt, te_gt


def tokenize(args, tr_data, te_data, tr_gt, te_gt):
    """Tokenize and filter dataset text. """

    tokenizer = TweetTokenizer(preserve_case=args.preserve_case)

    tr_tokens, te_tokens, tr_gt_tokens, te_gt_tokens = [], [], [], []
    dict_gt = {}

    for label, text in tr_data:



    [w if (not w.isdigit() and not isinstance(w, float)) or not pad_num else '<num>'
     for w in tokenizer.tokenize(text)]

    df_data = df_data[df_data.tokens.apply(lambda tokens: (len(tokens) > 0))]  # remove empty sentences
    print('\n\tMax sentence length:', args.max_len_text)
    print('\tTrain samples: {}, test samples: {}'
          .format(len(df_data[df_data.subset == 'train']), len(df_data[df_data.subset == 'test'])))

    return df_data



def extract_feature(tr_data, te_data, n_word_min):
    """ Preprocess word to index, and encode labels. """

    word2idx = get_word2idx(df_data.tokens.to_list(), n_word_min=n_word_min)
    x = transform_word2idx_mp(df_data.tokens.to_list(), word2idx=word2idx)
    y = pd.Categorical(df_data.label).codes

    return x, y, word2idx


def get_word2idx(text, n_word_min):
    """ Map words into indices."""

    word_counts = Counter([w for tokens in text for w in tokens])
    vocab = [w for w, v in word_counts.items() if v > n_word_min]

    word2idx = {word: i + 1 for i, word in enumerate(vocab)}
    word2idx['<pad>'], word2idx['<unk>'] = 0, len(vocab) + 1

    print('\tMost common words:', word_counts.most_common(10))
    print('\tTotal words:', len(vocab))
    return word2idx


def transform_word2idx_mp(tokens_of_texts, word2idx):
    with mp.Pool(mp.cpu_count()) as p:
        return p.starmap(transform_word2idx, map(lambda tokens: (tokens, word2idx), tokens_of_texts))


def transform_word2idx(tokens, word2idx):
    """ Convert word token to index. """

    unk_idx = len(word2idx) - 1
    return [word2idx.get(w) if word2idx.get(w) else unk_idx for w in tokens]


def get_embedding(args, word2idx):
    """ Find words in pretrained GloVe embeddings."""

    embeds_word = np.random.uniform(-np.sqrt(0.06), np.sqrt(0.06), (len(word2idx), args.d_pretrained))  # initializing
    emb_counts = 0

    if args.pretrained:
        for i, line in enumerate(codecs.open(args.path_pretrained, 'r', 'utf-8')):
            s = line.strip().split()
            if len(s) == (args.d_pretrained + 1) and s[0] in word2idx:
                embeds_word[word2idx[s[0]]] = np.array([float(i) for i in s[1:]])
                emb_counts += 1

    print('\tPretrained GloVe found:', emb_counts)
    return embeds_word


if __name__ == '__main__':
    main()
