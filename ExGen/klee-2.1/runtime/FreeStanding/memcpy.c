/*===-- memcpy.c ----------------------------------------------------------===//
//
//                     The KLEE Symbolic Virtual Machine
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===*/

#include <stdlib.h>

// void *memcpy(void *destaddr, void const *srcaddr, size_t len) {
//   char *dest = destaddr;
//   char const *src = srcaddr;

//   while (len-- > 0)
//     *dest++ = *src++;
//   return destaddr;
// }

void *memcpy(void *dest, void *src, unsigned int count) {
  if ((NULL == dest) || (NULL == src))
    return NULL;

  char *d = (char *)dest;
  char *s = (char *)src;

  // Check for overlapping buffers:
  if ((d <= s) || (d >= s + count)) {
    // Do normal (Upwards) Copy
    while (count-- > 0)
      *d++ = *s++;
  } else {
    // Do Downwards Copy to avoid propagation
    while (count > 0) {
      *(d + count - 1) = *(s + count - 1);
      --count;
    }
  }

  return dest;
}
