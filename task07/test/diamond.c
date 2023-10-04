#include <stdio.h>

int main() {
    int a = 47;
    int cond = 1;

    if (cond) {
        a = 1;
    } else {
        a = 2;
    }

    printf("%d\n", a);

    return 0;
}
