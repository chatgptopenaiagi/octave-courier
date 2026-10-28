## A small script with an independent expected matrix result.
A = [1, 2; 3, 4];
B = [5, 6; 7, 8];
C = A * B;
assert (isequal (C, [19, 22; 43, 50]));
disp (C);
