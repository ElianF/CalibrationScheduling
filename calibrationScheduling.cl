% computation basis
validComp(C, LO..HI) :- isCompInterval(C, LO, HI, A).
isComp(C) :- isCompInterval(C, LO, HI, A).

% measurements
isMess(1).
isMess(M+1) :- validMess(M, P, S, C),
               #count{'M : isCompUsed('M, C), 'M <= M} < A, isCompInterval(C, _LO, _HI, A),
               2*M < #sum{'A, 'C : isCompInterval('C, 'LO, 'HI, 'A)}.
validMess(M, P, S, C) :- validPump(P, S), isMess(M), validComp(C, 50), 
                         {validMess(M, P, _S, _C) : _C != C}0, % is pump used in this measurement
                         {validMess(M, _P, _S, C) : _P != P}0. % is comp used in this measurement
% not isPumpUsed(M, P), not isCompUsed(M, C), not isCompComplete(C)

% helper methods
isPumpUsed(M, P) :- validMess(M, P, _S, _C).
isCompUsed(M, C) :- validMess(M, _P, _S, C).
% isCompIncomplete(C) :- #count{'M : isCompUsed('M, C), isMess('M)} < A, isCompInterval(C, _LO, _HI, A).

% debugging