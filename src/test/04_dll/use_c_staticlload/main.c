#ifdef __cplusplus
#error "use C"
#endif // __cplusplus

#include "../mul.h"

#include <stdio.h>

int main() {
	int result = mul(2, 3);
	printf("mul(2, 3): %d\n", result);
	if (result != 6) {
		fprintf(stderr, "FAILED: expected 6, got %d\n", result);
		return 1;
	}
	return 0;
}
