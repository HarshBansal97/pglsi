# PostgreSQL plugin for latent semantic analysis

This is an experimental extension for latent semantic analysis.

## Installation

You need Python gensim module available. For non-standard import paths have a plpython function modify sys.path before calling load_lsi_model().

## Building the model

There is an example script for building a model. See `buildmodel.py`. You will minimally need adjust SQL in `get_messages()` function.

## Using it

First you need to load your model.

```sql
SELECT load_lsi_model('/path/to/my.model');
```

Step 2 is to transform your entries into feature space using `transform_to_model()`. Example:

```sql
INSERT INTO hackers_features 
SELECT box_id, msg_id, 
 transform_to_model(subject||' '||content) AS features 
FROM hackers_archive;
```

Step 3, find entries that are closest to your lookup document:

```sql
SELECT sender, subject, date, similarity
FROM hackers_archive NATURAL JOIN 
 (SELECT box_id, msg_id, 
   dotproduct(features, lookup_features) AS similarity
  FROM hackers_features, 
   (SELECT transform_to_model('wal checksum performance') 
     AS lookup_features) AS lookup
  ORDER BY similarity DESC
  LIMIT 50) 
 top_similarities;
```