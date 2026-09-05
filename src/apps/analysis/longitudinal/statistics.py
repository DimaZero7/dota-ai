"""Descriptive statistics and explicitly assumption-bound permutation screening."""
import math
import random
import statistics

from ..numeric.schemas import number


def quantile(values: list[float], probability: float) -> float | None:
    if not 0<=probability<=1:raise ValueError('Probability must be within [0,1]')
    if not values:return None
    xs=sorted(values);index=(len(xs)-1)*probability;lo=int(index);hi=min(lo+1,len(xs)-1)
    return xs[lo]+(xs[hi]-xs[lo])*(index-lo)


def describe(values: list[float | None]) -> dict:
    xs=[x for x in values if number(x)];n=len(xs);mid=quantile(xs,.5)
    return {'n':n,'missing':len(values)-n,'coverage':n/len(values) if values else None,
            'mean':statistics.mean(xs) if xs else None,'median':mid,'q25':quantile(xs,.25),
            'q75':quantile(xs,.75),'p10':quantile(xs,.1),'p90':quantile(xs,.9),
            'stddev':statistics.stdev(xs) if n>1 else None,
            'mad':statistics.median([abs(x-mid) for x in xs]) if xs else None,
            'min':min(xs,default=None),'max':max(xs,default=None),'sum':sum(xs),
            'small_sample':n<5,'quantile_method':'linear at (n-1)*p'}


def distribution(observations: list[dict | None]) -> dict:
    result=describe([m['value'] if m and m['eligible'] else None for m in observations])
    eligible=[m for m in observations if m and m['eligible'] and number(m['value'])]
    ratios=[m for m in eligible if number(m.get('numerator')) and number(m.get('denominator')) and m['denominator']>0]
    units={(m['unit'],m.get('scale',1)) for m in eligible}
    if len(units)>1:raise ValueError('Incompatible measurement units/scales')
    num=sum(m['numerator'] for m in ratios);den=sum(m['denominator'] for m in ratios)
    result.update(pooled_numerator=num if ratios else None,pooled_denominator=den if ratios else None,
                  denominator_range=[min((m['denominator'] for m in ratios),default=None),max((m['denominator'] for m in ratios),default=None)],
                  pooled_value=num/den*ratios[0].get('scale',1) if den else None,
                  pooled_n=len(ratios),unit=next(iter(units))[0] if units else None,
                  meaning='mean/quantiles weight matches equally; pooled value weights their denominators')
    return result


def correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs)!=len(ys):raise ValueError('Paired values required')
    if len(xs)<3:return None
    mx=statistics.mean(xs);my=statistics.mean(ys)
    a=sum((x-mx)**2 for x in xs);b=sum((y-my)**2 for y in ys)
    if a==0 or b==0:return None
    return max(-1,min(1,sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(a*b)))


def ranks(xs: list[float]) -> list[float]:
    ordered=sorted(enumerate(xs),key=lambda x:x[1]);result=[0.0]*len(xs);i=0
    while i<len(xs):
        j=i+1
        while j<len(xs) and ordered[j][1]==ordered[i][1]:j+=1
        for k in range(i,j):result[ordered[k][0]]=(i+j-1)/2+1
        i=j
    return result


def association(xs: list[float], ys: list[float]) -> dict:
    r=correlation(xs,ys)
    slope=None
    if len(xs)>1 and len(set(xs))>1:
        mx=statistics.mean(xs);my=statistics.mean(ys)
        slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
    return {'n':len(xs),'pearson':r,'spearman':correlation(ranks(xs),ranks(ys)),
            'slope_y_per_x':slope,'small_sample':len(xs)<5,'causal':False}


def permutation_p(xs: list[float], ys: list[float], *, seed: int, resamples: int = 999) -> float | None:
    """Two-sided |Pearson| under exchangeable paired observation labels, with +1 correction."""
    observed=correlation(xs,ys)
    if observed is None:return None
    if resamples<99:raise ValueError('At least 99 permutations required')
    rng=random.Random(seed);count=0
    # Precenter once; shuffling preserves marginal means and norms.
    mx=statistics.mean(xs);my=statistics.mean(ys)
    ax=[x-mx for x in xs];ay=[y-my for y in ys]
    denominator=math.sqrt(sum(x*x for x in ax)*sum(y*y for y in ay))
    for _ in range(resamples):
        shuffled=ay.copy();rng.shuffle(shuffled)
        score=sum(x*y for x,y in zip(ax,shuffled))/denominator
        count+=abs(score)>=abs(observed)-1e-12
    return (count+1)/(resamples+1)


def bonferroni(p: float | None, family_size: int) -> float | None:
    if family_size<1:raise ValueError('A declared comparison family is required')
    return min(1,p*family_size) if p is not None else None
