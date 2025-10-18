#include <stdio.h>
#include <stdlib.h>

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

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <num1> <num2>\n", argv[0]);
        return 1;
    }
    
    int num1 = atoi(argv[1]);
    int num2 = atoi(argv[2]);
    
    int result = compute(num1, num2);
    printf("Result: %d\n", result);
    
    return 0;
}