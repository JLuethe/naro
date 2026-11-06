/* Bounded ordinary-input exercise of the real C/FFI regex and byte helpers.
 * Patterns are fixed, benign expressions; no filesystem or terminal actions.
 */
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

void *nr_regex(const char *, int, char *, size_t);
int nr_match(void *, const char *, size_t, size_t, int, int *, int);
int nr_nsub(void *);
void nr_regex_free(void *);
int nr_byte_lower(int);
int nr_print_byte(int);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 4096) return 0;
    char *text = malloc(size + 1);
    assert(text);
    memcpy(text, data, size);
    text[size] = 0;
    const char *patterns[] = {"a", "(a)(b)?", "[[:alnum:]]+", "^$", "x*"};
    for (size_t p = 0; p < sizeof(patterns) / sizeof(patterns[0]); ++p) {
        char error[128];
        void *regex = nr_regex(patterns[p], 1, error, sizeof error);
        assert(regex);
        int count = nr_nsub(regex) + 1;
        assert(count >= 1 && count <= 10);
        size_t offsets[] = {0, size / 2, size};
        for (size_t i = 0; i < 3; ++i) {
            int pairs[20];
            for (int n = 0; n < 20; ++n) pairs[n] = -1;
            if (nr_match(regex, text, size, offsets[i], i != 0, pairs, count) == 0) {
                assert(pairs[0] >= (int)offsets[i] && pairs[1] <= (int)size);
                for (int n = 0; n < count; ++n) {
                    assert((pairs[2*n] == -1 && pairs[2*n+1] == -1) ||
                           (pairs[2*n] >= 0 && pairs[2*n] <= pairs[2*n+1] &&
                            pairs[2*n+1] <= (int)size));
                }
            }
        }
        nr_regex_free(regex);
    }
    for (size_t i = 0; i < size; ++i) {
        int lowered = nr_byte_lower(data[i]);
        assert(lowered >= 0 && lowered <= 255);
        (void)nr_print_byte(data[i]);
    }
    free(text);
    return 0;
}
