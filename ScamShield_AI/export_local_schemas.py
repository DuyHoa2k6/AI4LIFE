"""Export schemas from the actual Python types; no dataset labels are rewritten."""
import json
from pathlib import Path
from backend.local_reasoning.schema import LocalResult, DatasetCase
from backend.local_reasoning.interpretation_schema import Interpretation
from backend.local_reasoning.rule_schema import Rulebook


def main():
    root=Path(__file__).resolve().parent.parent/'data/v2'
    for name,model in [('output.schema.json',LocalResult),('case.schema.json',DatasetCase),
                       ('interpretation.schema.json',Interpretation),('rulebook.schema.json',Rulebook)]:
        (root/name).write_text(json.dumps(model.model_json_schema(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Exported 4 local schemas; dataset records untouched.')


if __name__=='__main__':main()
