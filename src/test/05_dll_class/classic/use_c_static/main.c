#include "../MyClass.h"

#include <stdlib.h>
#include <stdio.h>

int main() {
	size_t s = sizeof_MyClass();
	void* addr = malloc(s);
	MyClassHandle h = MyClass_Construct(addr);
	MyClass_SayHello(h);
	printf("(%d, %d)\n", h->x, h->y);
	if (h->x != 1 || h->y != 2) {
		fprintf(stderr, "FAILED: expected (1, 2), got (%d, %d)\n", h->x, h->y);
		MyClass_Destruct(h);
		free(addr);
		return 1;
	}
	MyClass_Destruct(h);
	free(addr);
	return 0;
}
