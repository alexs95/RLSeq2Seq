# coding=utf-8
# Copyright 2018 The Tensor2Tensor Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# coding=utf-8
"""ROUGE metric implementation.

This is a modified and slightly extended version of
https://github.com/miso-belica/sumy/blob/dev/sumy/evaluation/rouge.py.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re

import nltk
import numpy as np
import data
import tensorflow as tf

from modeling.score import FactCC


def _len_lcs(x, y):
  """Returns the length of the Longest Common Subsequence between two seqs.

  Source: http://www.algorithmist.com/index.php/Longest_Common_Subsequence

  Args:
    x: sequence of words
    y: sequence of words

  Returns
    integer: Length of LCS between x and y
  """
  table = _lcs(x, y)
  n, m = len(x), len(y)
  return table[n, m]


def _lcs(x, y):
  """Computes the length of the LCS between two seqs.

  The implementation below uses a DP programming algorithm and runs
  in O(nm) time where n = len(x) and m = len(y).
  Source: http://www.algorithmist.com/index.php/Longest_Common_Subsequence

  Args:
    x: collection of words
    y: collection of words

  Returns:
    Table of dictionary of coord and len lcs
  """
  n, m = len(x), len(y)
  table = dict()
  for i in range(n + 1):
    for j in range(m + 1):
      if i == 0 or j == 0:
        table[i, j] = 0
      elif x[i - 1] == y[j - 1]:
        table[i, j] = table[i - 1, j - 1] + 1
      else:
        table[i, j] = max(table[i - 1, j], table[i, j - 1])
  return table


def _f_lcs(llcs, m, n):
  """Computes the LCS-based F-measure score.

  Source: https://www.microsoft.com/en-us/research/publication/
  rouge-a-package-for-automatic-evaluation-of-summaries/

  Args:
    llcs: Length of LCS
    m: number of words in reference summary
    n: number of words in candidate summary

  Returns:
    Float. LCS-based F-measure score
  """
  r_lcs = llcs / m
  p_lcs = llcs / n
  beta = p_lcs / (r_lcs + 1e-12)
  num = (1 + (beta**2)) * r_lcs * p_lcs
  denom = r_lcs + ((beta**2) * p_lcs)
  f_lcs = num / (denom + 1e-12)
  return f_lcs


def rouge_l_sentence_level(vocab, scorer: FactCC):
  """Computes ROUGE-L (sentence level) of two collections of sentences.

  Source: https://www.microsoft.com/en-us/research/publication/
  rouge-a-package-for-automatic-evaluation-of-summaries/

  Calculated according to:
  R_lcs = LCS(X,Y)/m
  P_lcs = LCS(X,Y)/n
  F_lcs = ((1 + beta^2)*R_lcs*P_lcs) / (R_lcs + (beta^2) * P_lcs)

  where:
  X = reference summary
  Y = Candidate summary
  m = length of reference summary
  n = length of candidate summary

  Args:
    eval_sentences: The sentences that have been picked by the summarizer
    ref_sentences: The sentences from the reference set

  Returns:
    A float: F_lcs
  """

  def untokenize(sentence):
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.
    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    """
    step1 = sentence.replace("`` ", '"').replace(" ''", '"').replace('. . .', '...')
    step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
    step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
      "can not", "cannot")
    step6 = step5.replace(" ` ", " '")
    return step6.strip()

  def func(eval_sentences, ref_sentences, story_sentences, stories, abstracts, art_oovs):
    # tf.logging.info('eval: ' + str(len(eval_sentences)))
    # sents = []
    # for inx, sent in enumerate(eval_sentences):
    #   sent = data.outputids2words([int(word) for word in sent], vocab, art_oovs[inx].decode('utf-8').split(" "))
    #   sent = " ".join(sent)
    #   sents.append(sent.replace('[unk] ', ''))
    # tf.logging.info('eval: ' + str(sents))

    # tf.logging.info('ref: ' + str(len(ref_sentences)))
    # sents = []
    # for inx, sent in enumerate(ref_sentences):
    #   sent = data.outputids2words([int(word) for word in sent], vocab, art_oovs[inx].decode('utf-8').split(" "))
    #   sent = " ".join(sent)
    #   sents.append(sent.replace('[unk] ', ''))
    # tf.logging.info('reference: ' + str(sents))

    # tf.logging.info('abstracts: ' + str(len(abstracts)))
    # tf.logging.info('abstracts type: ' + str(type(abstracts)))
    # tf.logging.info('abstracts elem type: ' + str(type(abstracts[0])))
    # tf.logging.info('story_sentences: ' + str(len(story_sentences)))
    # tf.logging.info('story_sentences type: ' + str(type(story_sentences)))
    # tf.logging.info('story_sentences elem type: ' + str(type(story_sentences[0])))
    # tf.logging.info('story_sentences len(elem) elem type: ' + str(type(story_sentences[0][0])))
    # tf.logging.info('eval: ' + str(len(eval_sentences)))
    # tf.logging.info('eval type: ' + str(type(eval_sentences)))
    # tf.logging.info('eval elem type: ' + str(type(eval_sentences[0])))
    # tf.logging.info('eval elem elem type: ' + str(type(eval_sentences[0][0])))
    # tf.logging.info('stories: ' + str(len(stories)))
    # tf.logging.info('stories type: ' + str(type(stories)))
    # tf.logging.info('stories elem type: ' + str(type(stories[0])))
    # # tf.logging.info(abstracts)

    # Fix unk, fix -lrb-, -rrb-
    story_sents = []
    for inx, sent in enumerate(stories):
      sent = sent.decode("utf-8").replace('-lrb-', '(').replace('-rrb-', ')')
      story_sents.append(sent)
    # tf.logging.info('story: ' + str(story_sents[0]))

    eval_sents = []
    for inx, sent in enumerate(eval_sentences):
      sent = data.outputids2words([int(word) for word in sent], vocab, art_oovs[inx].decode('utf-8').split(" "))
      sent = " ".join(sent)
      eval_sents.append(untokenize(sent))
    # tf.logging.info('eval_sentences: ' + str(eval_sents[0]))

    # ref_sents = []
    # for inx, sent in enumerate(ref_sentences):
    #   sent = data.outputids2words([int(word) for word in sent], vocab, art_oovs[inx].decode('utf-8').split(" "))
    #   sent = " ".join(sent)
    #   ref_sents.append(untokenize(sent))
    # tf.logging.info('ref_sentences: ' + str(ref_sents[0]))

    factcc_scores = scorer.score([nltk.sent_tokenize(s) for s in story_sents], [nltk.sent_tokenize(s) for s in eval_sents])
    # factcc_scores_ref = scorer.score([nltk.sent_tokenize(s) for s in story_sents], [nltk.sent_tokenize(s) for s in ref_sents])

    f1_scores = []
    for eval_sentence, ref_sentence in zip(eval_sentences, ref_sentences):
      m = len(ref_sentence)
      n = len(eval_sentence)
      lcs = _len_lcs(eval_sentence, ref_sentence)
      f1_scores.append(_f_lcs(lcs, m, n))

    # print(f1_scores)
    # print(list(
    #   (factcc_scores.to_numpy() * 0.3) + (np.array(f1_scores).astype(np.float32) * 0.7)
    # ))
    # print(list(factcc_scores.to_numpy()))
    # print(list(factcc_scores.to_numpy() * 0.3))

    return (factcc_scores.to_numpy() * 0.05) + (np.array(f1_scores).astype(np.float32) * 0.95)

  return func


def rouge_l_fscore(hypothesis, references, **unused_kwargs):
  """ROUGE scores computation between labels and predictions.

  This is an approximate ROUGE scoring method since we do not glue word pieces
  or decode the ids and tokenize the output.

  Args:
    predictions: tensor, model predictions (batch_size, <=max_dec_steps)
    labels: tensor, gold output. (batch_size, max_dec_steps)

  Returns:
    rouge_l_fscore: approx rouge-l f1 score.
  """
  rouge_l_f_score = tf.py_func(rouge_l_sentence_level(unused_kwargs['vocab'], unused_kwargs["scorer"]), (hypothesis, references, unused_kwargs['enc_batch'], unused_kwargs['stories'], unused_kwargs['abstracts'], unused_kwargs['art_oovs']), [tf.float32])

  return rouge_l_f_score


def _get_ngrams(n, text):
  """Calculates n-grams.

  Args:
    n: which n-grams to calculate
    text: An array of tokens

  Returns:
    A set of n-grams
  """
  ngram_set = set()
  text_length = len(text)
  max_index_ngram_start = text_length - n
  for i in range(max_index_ngram_start + 1):
    ngram_set.add(tuple(text[i:i + n]))
  return ngram_set


def rouge_n(eval_sentences, ref_sentences, n=2):
  """Computes ROUGE-N f1 score of two text collections of sentences.

  Source: https://www.microsoft.com/en-us/research/publication/
  rouge-a-package-for-automatic-evaluation-of-summaries/

  Args:
    eval_sentences: The sentences that have been picked by the summarizer
    ref_sentences: The sentences from the reference set
    n: Size of ngram.  Defaults to 2.

  Returns:
    f1 score for ROUGE-N
  """

  f1_scores = []
  for eval_sentence, ref_sentence in zip(eval_sentences, ref_sentences):
    eval_ngrams = _get_ngrams(n, eval_sentence)
    ref_ngrams = _get_ngrams(n, ref_sentence)
    ref_count = len(ref_ngrams)
    eval_count = len(eval_ngrams)

    # Gets the overlapping ngrams between evaluated and reference
    overlapping_ngrams = eval_ngrams.intersection(ref_ngrams)
    overlapping_count = len(overlapping_ngrams)

    # Handle edge case. This isn't mathematically correct, but it's good enough
    if eval_count == 0:
      precision = 0.0
    else:
      precision = overlapping_count / eval_count

    if ref_count == 0:
      recall = 0.0
    else:
      recall = overlapping_count / ref_count

    f1_scores.append(2.0 * ((precision * recall) / (precision + recall + 1e-8)))

  # return overlapping_count / reference_count
  return np.array(f1_scores).astype(np.float32)


def rouge_2_fscore(predictions, labels, **unused_kwargs):
  """ROUGE-2 F1 score computation between labels and predictions.

  This is an approximate ROUGE scoring method since we do not glue word pieces
  or decode the ids and tokenize the output.

  Args:
    predictions: tensor, model predictions (batch_size, <=max_dec_steps)
    labels: tensor, gold output. (batch_size, max_dec_steps)

  Returns:
    rouge2_fscore: approx rouge-2 f1 score.
  """

  rouge_2_f_score = tf.py_func(rouge_n, (predictions, labels), [tf.float32])
  return rouge_2_f_score, tf.constant(1.0)
