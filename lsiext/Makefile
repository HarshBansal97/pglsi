MODULES = lsi
EXTENSION = lsi
EXTVERSION = 1.0.0
DATA = $(wildcard *--*.sql) $(EXTENSION)--$(EXTVERSION).sql
DOCS = 
REGRESS = 
EXTRA_CLEAN = $(EXTENSION)--$(EXTVERSION).sql
PG_CONFIG = pg_config

EXTRA_CLEAN = $(EXTENSION)--$(EXTVERSION).sql
all: $(EXTENSION)--$(EXTVERSION).sql

$(EXTENSION)--$(EXTVERSION).sql: $(EXTENSION).sql
	cp $< $@

PGXS := $(shell $(PG_CONFIG) --pgxs)

include $(PGXS)

