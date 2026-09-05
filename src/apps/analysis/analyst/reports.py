"""Render existing authored content; this module does not infer gameplay traits."""


def render_profile(profile: dict, *, language: str) -> str:
    if language not in ('ru','en'):raise ValueError('RU or EN required')
    ru=language=='ru';labels={
        'discovered':'обнаружена','testing':'проверяется','supported':'поддержана','weakened':'ослабла','rejected':'отвергнута'}
    lines=['# '+('Личный профиль: накопительный анализ' if ru else 'Personal profile: cumulative analysis'),'',
           ('Автор: текущий Codex. ' if ru else 'Author: current Codex. ')+
           (f"Игр в популяции: {profile['population_count']}; поколение статистики: {profile['generation']}." if ru else f"Population: {profile['population_count']} games; statistics generation: {profile['generation']}."),'',
           profile['portrait'][language],'','## '+('Что изменилось' if ru else 'What changed'),'',profile['change_reason'][language],'',
           '## '+('Направление развития' if ru else 'Development priorities'),'']
    for p in profile['priorities']:
        lines += [p['action'][language],'',p['baseline'][language],'',p['check'][language],'']
    lines+=['## '+('Основания и открытые вопросы' if ru else 'Evidence and open questions'),'']
    for h in profile['hypotheses']:
        lines += ['### '+h['id']+' — '+(labels[h['status']] if ru else h['status']),'',
                  h['statement'][language],'',h['alternative'][language],'',h['uncertainty'][language],'',h['criterion'][language],'',
                  ('Изменение: ' if ru else 'Change: ')+h['change'][language],'',
                  ('Основания: ' if ru else 'Evidence: ')+', '.join(h['support'])+'. '+
                  ('Контрпроверки: ' if ru else 'Counterchecks: ')+(', '.join(h['counterevidence']) or ('не раскрывались отдельно' if ru else 'not separately opened'))+'.','']
    lines+=['## '+('Границы' if ru else 'Limits'),'',profile['limitations'][language],'',
            ('Ревизия: ' if ru else 'Revision: ')+profile['revision'],
            ('Предыдущая версия: ' if ru else 'Previous revision: ')+str(profile['previous_revision']),'']
    return '\n'.join(lines)
