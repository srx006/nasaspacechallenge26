"""Research-only JP-06 contract fixture validation; not competition backend."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
root = Path(__file__).resolve().parent
schemas = root / 'contracts' / 'schemas'
cases = [('study-area','study-area-candidate'),('scene','scene-d084.catalog'),('analysis','analysis-d084-d085-NO-GO')]
for sk, example in cases:
    sch = json.loads((schemas / f'{sk}.schema.json').read_text(encoding='utf8'))
    instance = json.loads((root / 'contracts' / 'examples' / f'{example}.json').read_text(encoding='utf8'))
    resolver = RefResolver(base_uri=schemas.as_uri() + '/', referrer=sch)
    Draft202012Validator(sch, resolver=resolver, format_checker=FormatChecker()).validate(instance)
    print(f'PASS {example}')
print('Three structural fixtures validated; scientific QA not performed.')
