#include <stdio.h>

int main() {
    int a, b, c, d;

    a = 1;
    b = 2;
    c = a + b;
    b = 3;
    d = a + b;

    printf("%d\n", d);

    return 0;
}
