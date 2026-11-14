#define api_local static

api_local int helper(int v) { return v * 2; }

int run(int v) { return helper(v); }
