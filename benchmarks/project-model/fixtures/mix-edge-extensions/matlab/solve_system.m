function x = solve_system(A, b)
% SOLVE_SYSTEM Solve the linear system A*x = b.
%   x = SOLVE_SYSTEM(A, b) returns the least-squares solution.
x = A \ b;
end
