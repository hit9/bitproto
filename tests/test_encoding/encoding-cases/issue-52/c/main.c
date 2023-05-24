#include "a_bp.h"
#include "b_bp.h"
#include <assert.h>

int main(void) {
  struct A a = {.x = OK};
  assert(a.x == OK);
  return 0;
}
