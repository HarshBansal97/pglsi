#include <postgres.h>
#include "fmgr.h"
#include "utils/array.h"

#ifdef PG_MODULE_MAGIC
PG_MODULE_MAGIC;
#endif

PG_FUNCTION_INFO_V1(dotproduct_real);

Datum
dotproduct_real(PG_FUNCTION_ARGS)
{
    float8 sum = 0.0;
    int i;

    ArrayType  	  *a = PG_GETARG_ARRAYTYPE_P(0);
    float4* a_values = (float4*) ARR_DATA_PTR(a);

    ArrayType  *b = PG_GETARG_ARRAYTYPE_P(1);
    float4* b_values = (float4*) ARR_DATA_PTR(b);

    int a_count, b_count;

    if (ARR_NDIM(a) != 1 || ARR_NDIM(b) != 1)
    	ereport(ERROR,
    			(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
    			 errmsg("Arrays for dot product must be one dimensional")));

    a_count = ARR_DIMS(a)[0];
    b_count = ARR_DIMS(b)[0];

    if (a_count != b_count)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("Arrays for dot product must be the same length")));

    for (i = 0; i < a_count; i++) {
    	sum += a_values[i]*b_values[i];
    }

    PG_RETURN_FLOAT8(sum);
}
