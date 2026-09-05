"""Self-contained heatmaps over a pinned, explicitly versioned Dota underlay."""
from html import escape
from pathlib import Path

from .aggregation import summarize
from .terrain import load_underlay, project, cell_rectangle, underlay_label


def _color(value: float, maximum: float) -> str:
    weight=(min(1,abs(value)/maximum)**.5) if maximum else 0
    base=(31,113,145) if value<0 else (218,83,39)
    return '#'+''.join(f'{round(245+(v-245)*weight):02x}' for v in base)


def render_maps(*, group: dict, params: dict, title: str, output: Path, lang: str = 'ru', resources: bool = False,
                patch_id: int | None = None) -> None:
    ru=lang=='ru';stats=summarize(group,params);terrain=load_underlay()
    lo,hi=params['extent'];size=params['cell_size'];count=int((hi-lo)/size)
    panels=[('presence','Наблюдаемое время, с' if ru else 'Observed time, seconds'),
            ('death','Записанные смерти' if ru else 'Recorded deaths'),
            ('rate','Допущенные смерти / 10 мин' if ru else 'Eligible deaths / 10 minutes')]
    if resources:
        panels=[('farm','Добивания / наблюдаемую мин' if ru else 'Last hits / observed minute'),
                ('xp','Опыт / наблюдаемую мин' if ru else 'XP / observed minute'),
                ('damage','Урон героем / наблюдаемую мин' if ru else 'Hero damage / observed minute')]
    plot=420;panel_width=490;width=1480;height=770
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="#faf9f5"/>',
         '<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="#a5acb3" stroke-width=".7"/></pattern></defs>',
         '<g font-family="Arial,sans-serif" fill="#172631">',f'<text x="24" y="34" font-size="22" font-weight="bold">{escape(title)}</text>']
    svg.append(f'<defs><image id="terrain" width="{plot}" height="{plot}" xlink:href="{terrain["data_uri"]}"/><clipPath id="map-clip"><rect width="{plot}" height="{plot}"/></clipPath></defs>')
    svg.append(f'<text x="24" y="87" font-size="15" fill="#825017">{escape(underlay_label(lang=lang,patch_id=patch_id))}</text>')
    coverage=stats['coverage_fraction']
    caption=(f"Покрытие вне интервалов смерти: {coverage:.1%}" if ru else f"Coverage outside death intervals: {coverage:.1%}") if coverage is not None else ('Статус жизни неизвестен' if ru else 'Life status unknown')
    svg.append(f'<text x="24" y="61" font-size="14">{escape(caption)} | {stats["observed_outside_death_seconds"]:.0f} / {stats["outside_reported_death_seconds"]:.0f} s | n={stats["match_count"]}</text>')
    def value(x: dict | None, layer: str) -> float | None:
        if not x:return None
        if layer=='presence':return x['seconds']['outside_reported_death'] or None
        if layer=='death':return x['events']['death']['count'] or None
        if resources:
            e=x['events'][layer];exposure=e['exposure_seconds']
            return e['rate_value']*60/exposure if exposure>=params['minimum_exposure_seconds'] else None
        e=x['events']['death'];exposure=e['exposure_seconds']
        return e['rate_count']*600/exposure if exposure>=params['minimum_exposure_seconds'] else None
    for index,(layer,label) in enumerate(panels):
        ox=40+index*panel_width;oy=145
        values=[value(x,layer) for x in group['cells'].values()];maximum=max((abs(v) for v in values if v is not None),default=0)
        svg.append(f'<text x="{ox}" y="123" font-size="16" font-weight="bold">{escape(label)}</text>')
        svg.append(f'<g transform="translate({ox},{oy})" clip-path="url(#map-clip)"><use xlink:href="#terrain"/>')
        for iy in range(count):
            for ix in range(count):
                key=f'{ix},{iy}';data=group['cells'].get(key);v=value(data,layer)
                x,y,w,h=cell_rectangle(key,cell_size=size,plot_size=plot)
                if x>=plot or y>=plot or x+w<=0 or y+h<=0:continue
                fill='#ff541d' if v is None or v>=0 else '#36b5ff'
                opacity=.18+.57*(abs(v)/maximum)**.5 if v and maximum else 0
                event=data['events'][layer if resources else 'death'] if data else {}
                exp=event.get('exposure_seconds',0);raw=event.get('count',0);eligible=event.get('rate_count',0)
                tip=f'cell {key}; x=[{lo+ix*size},{lo+(ix+1)*size}); y=[{lo+iy*size},{lo+(iy+1)*size}); value={v}; events={raw}; eligible={eligible}; exposure={exp}s'
                svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" fill-opacity="{opacity}" stroke="#fff" stroke-opacity=".18" stroke-width=".6"><title>{escape(tip)}</title></rect>')
                if layer=='rate' and v is not None and eligible<params['minimum_deaths']:
                    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#hatch)" opacity=".5" pointer-events="none"/>')
                if layer=='death' and raw:
                    cx=min(plot-12,max(12,x+w/2));cy=min(plot-12,max(12,y+h/2))
                    svg.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="#a82018" stroke="#fff"/><text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" fill="#fff" font-weight="bold">{raw}</text>')
        svg.append('</g>')
        for tick in (64,96,128,160,191):
            px,_=project(tick,64,size=plot);_,py=project(64,tick,size=plot)
            x=ox+px;y=oy+py
            svg.append(f'<text x="{x}" y="{oy+plot+20}" text-anchor="middle" font-size="12">{tick}</text>')
            svg.append(f'<text x="{ox-8}" y="{y+4}" text-anchor="end" font-size="12">{tick}</text>')
        svg.append(f'<text x="{ox}" y="{oy+plot+44}" font-size="13">0 → {maximum:.2f} | cell {size}×{size} | Radiant ↙ / Dire ↗</text>')
    eligible=stats['events']['death']['rate_eligible_count'];deaths=stats['events']['death']['count']
    notes=([f'В частоту допущено {eligible} из {deaths} смертей: нужны сопоставимые координаты и покрытое время перед событием.',
            'Серый: нет наблюдаемого значения / недостаточно экспозиции. Штриховка: <60 с или <3 допущенных смертей.',
            'Координатная сетка источника, не рельеф Dota. Неизвестные интервалы не превращены во время на базе.',
            'Цвет частоты описывает отобранные наблюдения; он не доказывает опасность области или ошибку маршрута.'] if ru else
           [f'{eligible} of {deaths} deaths eligible for rates: comparable coordinates and covered pre-event exposure required.',
            'Gray: no observed value / insufficient exposure. Hatching: <60 seconds or <3 eligible deaths.',
            'Source-coordinate grid, not Dota terrain. Unknown intervals are not assigned to the base.',
            'Rate colors describe selected observations, not area danger or a route mistake.'])
    if resources:
        notes=([f"В частоты допущены: добивания {stats['events']['farm']['rate_eligible_count']}/{stats['events']['farm']['count']}, опыт {stats['events']['xp']['rate_eligible_value']}/{stats['events']['xp']['value']}, урон {stats['events']['damage']['rate_eligible_value']}/{stats['events']['damage']['value']}.",
                'Серый / штриховка: <60 с сопоставимого присутствия. Каждая панель имеет собственную шкалу.',
                'Опыт и добивания привязаны к свежей позиции игрока; урон — только атрибутированный исходному герою.',
                'Это интенсивность наблюдаемых событий, а не эффективность фарма или качество участия.'] if ru else
               [f"Eligible: last hits {stats['events']['farm']['rate_eligible_count']}/{stats['events']['farm']['count']}, XP {stats['events']['xp']['rate_eligible_value']}/{stats['events']['xp']['value']}, damage {stats['events']['damage']['rate_eligible_value']}/{stats['events']['damage']['value']}.",
                'Gray / hatching: <60 seconds of comparable exposure. Each panel has its own scale.',
                'XP and last hits use fresh player locations; damage is attributed to the original hero only.',
                'Observed event intensity, not farming efficiency or participation quality.'])
    notes[1]=('Без заливки: ноль или нет подходящего значения; частоты скрыты при <60 с. Штриховка: <3 допущенных смертей.' if ru else 'No fill: zero or no eligible value; rates hidden below 60 seconds. Hatching: <3 eligible deaths.')
    notes[2]=('Подложка: Valve / OpenDota 7.40. u=(x−64)/127, v=(191−y)/127. Кружки — суммы ячеек, не точные точки смерти.' if ru else 'Underlay: Valve / OpenDota 7.40. u=(x−64)/127, v=(191−y)/127. Circles are cell totals, not exact death points.')
    notes[3]=('Рельеф 7.41 может отличаться. Подложка обрезает отображение до [64,191]; полная статистика сохранена.' if ru else '7.41 terrain may differ. The underlay clips the view to [64,191]; full statistics are retained.')
    for i,line in enumerate(notes):svg.append(f'<text x="24" y="{650+i*23}" font-size="14">{escape(line)}</text>')
    svg.append('</g></svg>');output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(svg),encoding='utf-8')
