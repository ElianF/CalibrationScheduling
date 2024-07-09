% computation basis
isMess(1..X) :- X' = #sum{_N, _C : defComp(_C, _Lo, _Hi, _N, _Z)}, X = X' / 2.
isPump(P) :- validPump(P, S).
isComp(C) :- defComp(C, Lo, Hi, N, Z).

% generate solutions
{validMess(M, P, S, C)} :- isMess(M), validPump(P, S), isComp(C).

% hard constraints
%% general
% every component is measured often enough
countMessComp(C, Nreal) :- Nreal = #count{_M : validMess(_M, _P, _S, C)}, isComp(C).
:- countMessComp(C, Nreal), Nreal < N, defComp(C, Lo, Hi, N, Z).

%% per measurement
% at least two compounts are measured
:- X = #count{_C : validMess(M, _P, _S, _C)}, 0 < X, X < 2, isMess(M).

% remove redundant measurement due to symmetry
id1Mess(M, X) :- X = #sum{_Z : validMess(M, _P, _S, _C), defComp(_C, _Lo, _Hi, _N, _Z)}, isMess(M).
id2Mess(M, X) :- X = #sum{_S : validMess(M, _P, _S, _C)}, isMess(M).
:- U < V, id1Mess(M, U), id1Mess(M+1, V).
:- U == V, K < L, id1Mess(M, U), id1Mess(M+1, V), id2Mess(M, K), id2Mess(M+1, L).
:- validMess(M, P, S, C), validMess(M, P', S', C'), P >  P', S = S', C <  C'.
:- validMess(M, P, S, C), validMess(M, P', S', C'), P >  P', S = S', C >  C'.
:- validMess(M, P, S, C), validMess(M, P', S', C'), P <  P', S = S', C >  C'.

% ratios are within interval
isRatio(M, C, R) :- validMess(M, P, S, C), Sges = #sum{_S: validMess(M, _P, _S, _C)}, R = S * 100 / Sges, 0 <= R, R <= 100.
:- isRatio(M, C, R), defComp(C, Lo, Hi, N, Z), R < Lo.
:- isRatio(M, C, R), defComp(C, Lo, Hi, N, Z), Hi < R.

% uniqueness
:- validMess(M, P, S, C), validMess(M, P', S', C'), P  = P',          C != C'. % every pump gets unique component 
:- validMess(M, P, S, C), validMess(M, P', S', C'), P != P',          C  = C'. % every compount gets unique pump 
:- validMess(M, P, S, C), validMess(M, P', S', C'), P  = P', S != S'         . % every pump gets unique setting

% soft constraints
% optimize arrangement of measurements
#minimize{ 1 * 100 * X @1, M : validMess(M, P, S, C), X = 3}.
% maximize coverage of ratios in interval
maximalDistance(C, Dmax) :- isComp(C), 
                            Dmax = #max{|_R-_R'| : isRatio(_M, C, _R), isRatio(_M', C, _R'), _M != _M'}.
#maximize{ 2 * 100 * Dmax / (Hi-Lo) @2, C : 
               maximalDistance(C, Dmax), 
               defComp(C, Lo, Hi, N, Z)}.
% minimize variance through maximizing minimal distance between ratios
minimalDistance(C, Dmin) :- isComp(C),
                            Dmin = #min{|_R-_R'| : isRatio(_M, C, _R), isRatio(_M', C, _R'), _M != _M'}.
#maximize{ 1 * 100 * Dmin*(Nreal-1) / (Hi-Lo) @2, C : 
               minimalDistance(C, Dmin), 
               defComp(C, Lo, Hi, N, Z),
               countMessComp(C, Nreal)}.