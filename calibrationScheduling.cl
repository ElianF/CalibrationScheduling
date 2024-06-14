% computation basis
isMess(1..X) :- 2*X = #sum{N, C : defComp(C, Lo, Hi, N)}.
isPump(P) :- validPump(P, S).
isSetting(S) :- validPump(P, S).
isComp(C) :- defComp(C, Lo, Hi, N).

% generate solutions
{validMess(M, P, S, C)} :- isMess(M), isPump(P), isSetting(S), isComp(C).

% hard constraints
%% general
% every component is measured often enough
:- #count{_M : validMess(_M, _P, _S, C)} < N, defComp(C, Lo, Hi, N).
%% per measurement
% ratios are within interval
:- validMess(M, P, S, C), defComp(C, Lo, Hi, N), Sges = 50, R = S/Sges * 100, R < Lo, Hi < R.
% each component is unique for every pump
:- validMess(M, P, S, C), validMess(M, P, S', C'), C != C'.
% each setting is unique for every pump
:- validMess(M, P, S, C), validMess(M, P, S', C'), S != S'.