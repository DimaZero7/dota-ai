"""Review budgets, explicit meanings and authored-response contracts."""
from ..cumulative.schemas import encode, CumulativeError
from ..evidence import digest

VERSION='analyst-review-1'
DEFAULT_METRICS=('xp_rate','gold_rate','death_fraction','participation','repeat_death_fraction','tower_damage_rate')
DEFINITIONS={
    'xp_rate':('XP/min','Recorded XP / match or phase exposure ×60','Higher recorded acquisition; not necessarily better decisions; incomplete journals and level caps can matter.'),
    'gold_rate':('gold/min','Recorded gold / exposure ×60','Higher recorded acquisition; source event reasons differ from final GPM, not a conversion-to-win score.'),
    'death_fraction':('fraction','Reported death-interval seconds / exposure','Higher means more recorded unavailable time; 0.10=10%. Death is not automatically an error; duration and team conditions confound outcome.'),
    'participation':('fraction','Final kills+assists / team kills','Higher involvement in team kills, not complete fight participation or correct positioning.'),
    'repeat_death_fraction':('fraction','Deaths within 120s of previous reported death end / observed deaths','Higher recurrence; denominator is deaths, not opportunities to play safely. Zero deaths is undefined.'),
    'tower_damage_rate':('tower damage/min','Recorded tower damage / exposure ×60','Higher recorded building damage; tower availability, hero, team state and duration differ.'),
    'xp_team_share':('fraction','Phase recorded XP / recorded allied XP','Higher share of observed allied XP; not proof of taking resources away from allies.'),
    'post_combat_xp_change':('XP/min change','Next-current XP contrast: combat vs controls, matched phase/pre-state/death/baseline band','Higher relative contrast; overlapping windows/reused controls; regression to mean and confounding remain.'),
    'purchase_route_change':('total variation','Cell-distribution difference before/after recorded purchase','Higher route change, not item use/effect; purchase is not delivery and geometry is approximate.'),
    'space_concentration':('fraction','Largest presence cell exposure / observed exposure outside reported death','Higher concentration in one native grid cell; not passivity. Requires spatial coverage and map context.'),
    'transitions_per_min':('transitions/min','Native cell transitions / observed exposure ×60','Higher grid crossing frequency, not mobility quality or wasted movement.'),
    'return_delay':('seconds','Observed post-respawn activity delays / eligible returns','Higher observed delay, not proven inactivity; missing activity/right censoring matter.'),
    'deaths_per_10min':('deaths/10min','Observed deaths / exposure ×600','Higher observed death frequency; not independent mistakes.'),
}
READING_RULES=[
    'n counts eligible matches in this group; coverage is eligible/observed members, not completeness of all account games.',
    'Equal-match means/quantiles and pooled numerators/denominators answer different questions. Keep both.',
    'Group by hero/estimated position/version; side, rank, duration and drafts may remain uncontrolled. No causal or psychological label from a scalar.',
    'Small samples and outcome arms below five are descriptive. Stale screening supplies no current significance claim.',
    'Author connects patterns, alternatives and testable growth directions. No mandatory narration at lower levels.',
    'Local byte accounting does not isolate current Codex memory or measure exact model tokens. Previously seen material is not a blind test.',
]
STATES={'discovered','testing','supported','weakened','rejected'}
TRANSITIONS={
    'discovered':{'discovered','testing','weakened','rejected'},
    'testing':STATES,
    'supported':{'supported','testing','weakened','rejected'},
    'weakened':{'weakened','testing','supported','rejected'},
    'rejected':{'rejected','testing'},
}


class AnalystError(CumulativeError):
    """Stale review, missing evidence, invalid authored transition or exhausted budget."""


def size(value: object) -> int:
    return len(encode(value).encode('utf-8'))


def text(value: object, name: str, limit: int = 3000) -> None:
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise AnalystError(f'Nonempty bounded {name} required')


def bilingual(value: object, name: str) -> None:
    if not isinstance(value,dict) or set(value)!={'ru','en'}:raise AnalystError(f'RU/EN {name} required')
    for v in value.values():text(v,name)


def response_shape(response: dict, previous: dict | None, evidence: dict) -> None:
    if response.get('author')!='current Codex':raise AnalystError('Explicit current Codex authorship required')
    if size(response)>24000:raise AnalystError('Authored answer exceeds 24000 bytes')
    for key in ('portrait','limitations','change_reason'):bilingual(response.get(key),key)
    hypotheses=response.get('hypotheses');old={h['id']:h for h in (previous or {}).get('hypotheses',[])}
    if not isinstance(hypotheses,list) or not 1<=len(hypotheses)<=6:raise AnalystError('One to six hypotheses required')
    if len({h['id'] for h in hypotheses})!=len(hypotheses) or not set(old)<={h['id'] for h in hypotheses}:
        raise AnalystError('Unique hypotheses required; prior hypotheses must be retained, including rejected ones')
    for h in hypotheses:
        text(h.get('id'),'hypothesis id',80)
        for key in ('statement','alternative','criterion','uncertainty','decision_reason','change'):bilingual(h.get(key),key)
        if not isinstance(h.get('scope'),dict) or not h['scope'].get('position') or not h['scope'].get('hero_id'):
            raise AnalystError('Explicit hero and position scope required')
        state=h.get('status');prior=old.get(h['id'])
        if state not in (TRANSITIONS[prior['status']] if prior else {'discovered','testing'}):raise AnalystError('Invalid hypothesis lifecycle transition')
        support=h.get('support');counter=h.get('counterevidence')
        if not isinstance(support,list) or not support or not isinstance(counter,list):raise AnalystError('Support and explicit counterevidence list required')
        if not set(support+counter)<=set(evidence):raise AnalystError('Hypothesis cites evidence not delivered in this review')
        # Referencing the same evidence again cannot itself upgrade a hypothesis.
        if state=='supported' and (not prior or prior['status']!='supported'):
            if not any((previous or {}).get('evidence',{}).get(k)!=evidence[k] for k in support+counter):
                raise AnalystError('Upgrade requires newly versioned evidence, not repeated prose')
        if h.get('confidence') not in ('preliminary','conditional'):raise AnalystError('Prototype confidence must remain preliminary/conditional')
    priorities=response.get('priorities')
    if not isinstance(priorities,list) or not 1<=len(priorities)<=3:raise AnalystError('One to three growth priorities required')
    for p in priorities:
        for key in ('action','baseline','check'):bilingual(p.get(key),key)
        if not p.get('hypotheses') or not set(p['hypotheses'])<={h['id'] for h in hypotheses if h['status']!='rejected'}:
            raise AnalystError('Growth priority must reference active hypotheses')
    if response.get('wording') not in ('retain','revise'):raise AnalystError('Explicit retain/revise decision required')
    if response['wording']=='retain' and (not previous or response['portrait']!=previous['portrait']):
        raise AnalystError('Retaining wording requires the unchanged previous portrait')
