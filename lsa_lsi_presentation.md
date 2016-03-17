% Experimenting with Latent Semantic Analysis
% Hans-Jürgen Schönig
% www.postgresql-support.de

# Challenges people are facing

## Typical problems

- People are not exactly looking for the right words
- Specific word combinations do not occur
- Not all words are created equal


## An example

- Give me 50 hits for "hotel cheap"

- Performing normal full-text search is easy 
  and works very well in PostgreSQL.

- What if there are only 25 documents containing both words?


## The burden of "OR"

- Using OR is not an option here
- You do not want to find cheap phones
  when looking for a hotel

- In a way "hotel" is more relevant than "cheap"


## Word relevance

- How can you know, which words are related?
- How can you know, how relevant a word actually is?


## Ambiguous meanings

- Consider the following search strings:
	- "apple computer"
	- "apple food"

- There is more than one meaning of "apple".


## An algorithm is needed

- We need to find:
	- Relationships between words
	- Make sure their meaning is not ambiguous
	- Somewhat scale out during training


# Latent Semantic Indexing (LSI)

## Latent Semantic Indexing

- Concepts for LSI have been around for quite a while
- Mid-1960s: Factor analysis technique first described and tested
- 1988: Seminal paper on LSI technique published
- Patented in 1998 (US Patent 4,839,853, now expired) 


## How it works (1):

- A "corpus" is created
	- A corpus is a collection of documents
- A model is trained
- The model returns a list of document IDs
	- Similar documents are returned


## How it works (2):

- LSI uses linear algebra techniques to learn the conceptual 
  correlations in a collection of text
- A weighted term-document matrix is constructed
- Singular Value Decomposition (SVD) on the matrix is performed
- The matrix is used to identify the concepts contained in the text

- It is all about "dimensionality reduction"


## What it means 

- Dimensionality reduction is about mapping
  large number of words to a smaller set of 
  "concepts".

- For example: "apple computer imac desktop osx" belong together



## The key question

- Can we use it in PostgreSQL?
- Can we improve results?
- Can we make it scale?


## Implementations available

- There are some implementations out there
	- gensim (Python) seems the most promising one


## Trouble ahead (1)

- Finding nearest neighbors sounds like KNN

- The trouble is:
	- KNN indexing works with 1-3 dimensions
	- We got countless dimensions here

- KNN indexing is therefore not an option at all


## Trouble ahead (2)

- Writing an operator class is somewhat hard
- Indexes available in PostgreSQL are not very well suited
  for a model like that

- Reason: Curse of dimensionality, etc.


## Approaching the problem

- Creating reasonably small models to fit into memory
- Create a fast operator for sequential scanning
- Calculate similarity with all documents
- Use "top-N heapsort" capability of PostgreSQL


# Training the model

## Creating models

- Using Python gensim is the easiest way to train models
- Training is expensive
- gensim can scale out to many servers


## Time needed for training

- Training on Wikipedia takes around 12 hours
  on a 4 core workstation

- Wikipedia:
	- around 4 million articles
	- most frequent words (exactly 250k)
	- additional words are chopped off by gensim


## Models and sizes

- Models can be kept reasonably small:
	- 100 concepts: 20 MB
	- this a reasonable model for "PostgreSQL hackers"
	
- Size depends on:
	- words x concepts
	- It does NOT depend on the size of the corpus
	- It is all about generalization


## How to do it

- Select the content and some id and feed it to gensim
- gensim does the stemming
- gensim builds a dictionary
- Transform documents into Term-Document Sparse-Matrix
  (terms x documents)
- Run training
- Transform documents into model-space
 

## What is a "model space"?

- How much of each "concept" ("topic") is represented in each document?
- Example: Document is "12% X", "9% Y", ...

- It is a vector of numbers (floats)


## How search works

- Calculate the distance between the document and the query
- Transform a query into model space
- For each document we find the angle between the document and the query topics

- How to find the "angle"?
    - Use the "dot product" of both sides

`dot(a,b) = len(a)*len(b)*cos(phi)`
`len( a ) = len( b ) = 1`


## Now in SQL

- Build the document vectors:

```sql
INSERT INTO hackers_features 
SELECT box_id, msg_id, 
 transform_to_model(subject||' '||content) AS features 
FROM hackers_archive;
```


## Query

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


## Quality of results

- Results are what somewhat mixed
- For "hackers" it was not too useful
- It returned similar stuff 

- For Wikipedia results are somewhat better

- It really depends on the corpus
- Some preprocessing might be necessary


# Finally

## Questions

- Any questions?



