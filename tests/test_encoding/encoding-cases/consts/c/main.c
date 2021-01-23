#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "consts_bp.h"

int main(void) {
    assert(A == 1);
    assert(B == 6);
    assert(strcmp(C, "string") == 0);
    assert(D == true);
    assert(E == false);
    assert(F == true);
    assert(G == false);
    return 0;
}
