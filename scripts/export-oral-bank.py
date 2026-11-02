"""Build-time only; export original local task data without Python runtime dependencies."""
import ast, json, pathlib, sys
root=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'oral-assistant'))
import exam,question_bank
tree=ast.parse((root/'oral-assistant/evaluation.py').read_text(encoding='utf-8'))
scope={}
for item in tree.body:
    if isinstance(item,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('ITEM','SCHEMA') for t in item.targets):
        exec(compile(ast.Module(body=[item],type_ignores=[]),'<evaluation-schema>','exec'),scope)
(root/'native/evaluation-schema.json').write_text(json.dumps(scope['SCHEMA'],ensure_ascii=False,indent=2),encoding='utf-8')
bank=dict(stages=exam.STAGES,scenes=exam.SCENES,keywords=question_bank.KEYWORDS,intro=question_bank.INTRO,version=question_bank.VERSION,sources=question_bank.SOURCES)
for func in tree.body:
    if isinstance(func,ast.FunctionDef) and func.name=='context':
        for item in ast.walk(func):
            if isinstance(item,ast.Dict):
                for key,value in zip(item.keys,item.values):
                    if isinstance(key,ast.Constant) and key.value=='instruction':bank['evaluationInstruction']=ast.literal_eval(value)
(root/'src/oral/bank-full.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf-8')
print('题库与评价结构已导出')
