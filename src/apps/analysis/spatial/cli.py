"""Build local spatial maps, filtered cohorts, or selected action routes."""
import argparse
import json
from pathlib import Path

from ..numeric.storage import write_json, load_node
from .services import build_spatial_match, aggregate_selection, route_for_action
from .rendering import render_maps
from .aggregation import compact_selection


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--match-id',type=int);parser.add_argument('--all',action='store_true')
    parser.add_argument('--hero-id',type=int);parser.add_argument('--position');parser.add_argument('--side',choices=('radiant','dire'))
    parser.add_argument('--phase',type=int);parser.add_argument('--state',choices=('ahead','behind','near_even','unknown'))
    parser.add_argument('--output',type=Path,default=Path('data/analysis/spatial/selection.json'))
    parser.add_argument('--svg',type=Path);parser.add_argument('--lang',choices=('ru','en'),default='ru')
    parser.add_argument('--resources',action='store_true');parser.add_argument('--compact',action='store_true')
    parser.add_argument('--route-kind',choices=('death','purchase','ability','item','kill'));parser.add_argument('--source-index',type=int)
    args=parser.parse_args()
    if args.all==bool(args.match_id):parser.error('Choose exactly one of --all or --match-id')
    if (args.route_kind is None)!=(args.source_index is None) or (args.route_kind and args.all):parser.error('Route requires one match, kind and source index')
    if args.route_kind and (args.svg or args.compact):parser.error('Choose a route or a map/summary output')
    root=Path.cwd();selection=json.loads((root/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    ids=[int(k) for k in selection['lower_outputs']] if args.all else [args.match_id]
    results=[build_spatial_match(root=root,match_id=mid,account_id=selection['account_id']) for mid in ids]
    filters={key:getattr(args,key) for key in ('hero_id','position','side','phase','state') if getattr(args,key) is not None}
    aggregate=aggregate_selection([(r['match'],r['phases']) for r in results],filters=filters)
    if args.svg:
        if len(results)==1 and not filters:
            render_maps(group=results[0]['match']['distribution'],params=results[0]['match']['parameters'],title=f"Match {ids[0]} | native coordinates",output=args.svg,lang=args.lang,resources=args.resources,patch_id=results[0]['match']['context']['patch_ids']['opendota'])
        elif len(aggregate['groups'])==1:
            g=aggregate['groups'][0];matched=next(r for r in results if r['match']['context']['match_id'] in g['distribution']['match_ids']);render_maps(group=g['distribution'],params=aggregate['parameters'],title=str(g['context']),output=args.svg,lang=args.lang,resources=args.resources,patch_id=matched['match']['context']['patch_ids']['opendota'])
        else:parser.error('--svg needs one match without filters or exactly one resulting context group')
    if args.route_kind:
        directory=results[0]['directory'];manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        route=route_for_action(facts=load_node(root/manifest['numeric_bundle'],1),observations=results[0]['observations'],kind=args.route_kind,source_index=args.source_index)
        write_json(args.output,route)
    else:write_json(args.output,compact_selection(aggregate) if args.compact else aggregate)
    print(json.dumps({'matches':len(results),'groups':len(aggregate['groups']),'output':str(args.output),'new_matches_fetched':0}))


if __name__=='__main__':
    try:main()
    except (ValueError,FileNotFoundError) as error:raise SystemExit(f'Spatial analysis failed: {error}') from error
