import re
import os
import sys
import logging
import multiprocessing
from optparse import OptionParser

import psycopg2

from gensim import utils, corpora, models, similarities

url_re = re.compile(r'(?:https?|ftp)://\S+')

DEFAULT_DICT_SIZE = 100000
ARTICLE_MIN_WORDS = 20

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logging.root.setLevel(level=logging.INFO)

log = logging.getLogger('main')

class PsqlCorpus(corpora.TextCorpus):
    """Adapter to query model data from PostgreSQL."""
    def __init__(self, conn, processes=None):
        self.conn = conn

        self.metadata = False
        self.lemmatize = False
        if processes is None:
            processes = max(1, multiprocessing.cpu_count() - 1)
        self.processes = processes


        self.dictionary = corpora.Dictionary(self.get_texts())

    def get_texts(self):
        texts = ((content, self.lemmatize, subject, pageid) for subject, content, pageid in get_messages(self.conn))
        pool = multiprocessing.Pool(self.processes)
        
        posts, token_count = 0, 0
        for group in utils.chunkize(texts, chunksize=10 * self.processes, maxsize=1):
            for tokens, title, pageid in pool.imap(process_post, group):
                if len(tokens) < ARTICLE_MIN_WORDS:
                    continue
                if self.metadata:
                    yield (tokens, (repr(pageid), title))
                else:
                    yield tokens
                posts += 1
                token_count += len(tokens) 
        pool.terminate()
        
        log.info("Processed %d posts with %d tokens", posts, token_count)

def get_messages(conn):
    """Query data to process from postgresql"""
    cur = conn.cursor(name="archives")
    cur.execute("SELECT box_id, msg_id, subject, content FROM hackers_archive")
    for box_id, msg_id, subject, content in cur:
        yield subject, content, (box_id,msg_id)
    cur.close()
            
def process_post(args):
    """Normalize an entry into tokens"""
    content, lemmatize, subject, pageid = args
    text = url_re.sub('', subject + " " + content)
    
    if lemmatize:
        result = utils.lemmatize(text)
    else: 
        result = [token.encode('utf8') for token in
            utils.tokenize(text, lower=True, errors='ignore')
            if 2 <= len(token) <= 15 and not token.startswith('_')
        ]

    return result, subject, pageid

def process(prefix, connstr):
    # Create dictionary
    corpus = PsqlCorpus(psycopg2.connect(connstr))

    corpus.dictionary.filter_extremes(no_below=20, no_above=0.1, keep_n=DEFAULT_DICT_SIZE)
    corpus.dictionary.save_as_text(prefix+'_wordids.txt.bz2')
    
    corpora.MmCorpus.serialize(prefix+'_bow.mm', corpus, progress_cnt=10000)
    
    mm = corpora.MmCorpus(prefix + '_bow.mm')
    
    tfidf = models.TfidfModel(mm, id2word=corpus.dictionary, normalize=True)
    tfidf.save(prefix + '.tfidf_model')
    
    corpora.MmCorpus.serialize(prefix + "_tfidf.mm", tfidf[mm], progress_cnt=10000)
    log.info("Done processing input data")

def model(id2word, corpus, prefix, topics):
    lsi = models.LsiModel(corpus=corpus, id2word=id2word, num_topics=topics)
    lsi.save(prefix+".lsimodel")

    # Index not needed for now
    #if not os.path.exists(prefix+'_lsi_index'):
    #    os.mkdir(prefix+'_lsi_index')
        
    #index = similarities.Similarity(prefix+'_lsi_index/'+prefix+'_index', lsi[corpus], topics)
    #index.save(prefix+'_lsi_index/'+prefix+'_index')
    log.info("Done building model")

if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog --prefix=outputfileprefix [options]")
    parser.add_option("-c", "--connstr", dest="connstr",
                  help="Connect to CONNSTR to receive data", metavar="CONNSTR",
                  default="host=localhost")
    parser.add_option("-p", "--prefix", dest="prefix",
                  help="Store model with specified prefix")
    parser.add_option("-m", "--model-only", dest="modelonly", action='store_true',
                  help="Don't reprocess input data")
    parser.add_option("-i", "--corpus", dest="corpus",
                  help="Prefix for storing corpus. Useful when rebuilding model without reprocessing input data.")
    parser.add_option("-f", "--features", dest="features", type="int",
                  help="Number of features in the model.", default=100)
    (options, args) = parser.parse_args()
    
    if not options.prefix:
        parser.print_usage()
        sys.exit(1)
    
    corpus_prefix = options.corpus
    if corpus_prefix is None:
        corpus_prefix = options.prefix
    
    model_prefix = options.prefix
    
    if not options.modelonly:
        process(prefix=corpus_prefix, connstr=options.connstr)
    id2word = corpora.Dictionary.load_from_text(corpus_prefix+'_wordids.txt.bz2')
    corpus = corpora.MmCorpus(corpus_prefix + '_tfidf.mm')
    model(id2word, corpus, prefix=model_prefix, topics=options.features)