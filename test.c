#include <stdio.h>

int compute(int a, int b) {
    int result = 0;
    for (int i = 0; i < b; i++) {
        result += a * i;
    }
    if (result % 2 == 0) {
        result += 3;
    } else {
        result -= 2;
    }
    return result;
}

int main() {
    int x = 5;
    int y = 4;
    int res = compute(x, y);
    printf("Result: %d\n", res);
    return 0;
}
