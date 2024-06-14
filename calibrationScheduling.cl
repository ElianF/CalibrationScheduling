% computation basis
isMess(1..X) :- X' = #sum{_N, _C : defComp(_C, _Lo, _Hi, _N, _Z)}, X = (X'+1) / 2.
isPump(P) :- validPump(P, S).
isComp(C) :- defComp(C, Lo, Hi, N, Z).

% generate solutions
{validMess(M, P, S, C)} :- isMess(M), validPump(P, S), isComp(C).

% hard constraints
%% general
% every component is measured often enough
:- #count{_M : validMess(_M, _P, _S, C)} < N, defComp(C, Lo, Hi, N, Z).
%% per measurement
% remove redundant measurement due to symmetry
id1Mess(M, X) :- X = #sum{_Z : validMess(M, _P, _S, _C), defComp(_C, _Lo, _Hi, _N, _Z)}, isMess(M).
id2Mess(M, X) :- X = #sum{_S : validMess(M, _P, _S, _C)}, isMess(M).
:- U < V, id1Mess(M, U), id1Mess(M+1, V).
:- U == V, K <= L, id1Mess(M, U), id1Mess(M+1, V), id2Mess(M, K), id2Mess(M+1, L).
% ratios are within interval
:- validMess(M, P, S, C), defComp(C, Lo, Hi, N, Z), Sges = #sum{_S: validMess(M, _P, _S, _C)}, S*100 < Lo*Sges.
:- validMess(M, P, S, C), defComp(C, Lo, Hi, N, Z), Sges = #sum{_S: validMess(M, _P, _S, _C)}, Hi*Sges < S*100.
% uniqueness
:- validMess(M, P, S, C), validMess(M, P', S', C'), P  = P',          C != C'. % every pump gets unique component 
:- validMess(M, P, S, C), validMess(M, P', S', C'),          S != S', C  = C'. % every component gets unique setting