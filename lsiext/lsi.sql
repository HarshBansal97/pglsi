CREATE OR REPLACE FUNCTION load_lsi_model(path text) RETURNS text 
AS $$
    import gensim
    GD['lsi_model'] = lsi = gensim.models.LsiModel.load(path)
    return "Model with %d topics and %d terms" % (lsi.num_topics, lsi.num_terms)
$$ LANGUAGE plpython2u;

CREATE OR REPLACE FUNCTION transform_to_model(words text[]) RETURNS real[]
AS $$
    lsi = GD['lsi_model']
    bow = lsi.id2word.doc2bow(words)
    return [v for k,v in lsi[bow]]
$$ LANGUAGE plpython2u;

CREATE OR REPLACE FUNCTION transform_to_model(document text) RETURNS real[]
AS $$
    import re
    text = re.sub(r'(?:https?|ftp)://\S+', '', document)
    from gensim import utils
    words = [token.encode('utf8') for token in
        utils.tokenize(text, lower=True, errors='ignore')
        if 2 <= len(token) <= 15 and not token.startswith('_')
    ]
    
    lsi = GD['lsi_model']
    bow = lsi.id2word.doc2bow(words)
    return [v for k,v in lsi[bow]]
$$ LANGUAGE plpython2u;

CREATE OR REPLACE FUNCTION "dotproduct" (real[], real[]) 
RETURNS double precision
AS 'MODULE_PATHNAME', 'dotproduct_real' 
LANGUAGE C STRICT IMMUTABLE;

