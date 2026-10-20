import sys,re,os,json,hashlib
from pathlib import Path
a=sys.argv[1:];q=None
if '-q' in a:i=a.index('-q');q=[t.lower() for t in a[i+1].split(',') if t.strip()];a=a[:i]+a[i+2:]
R=Path(a[0] if a else '.').resolve();O=R/'.codemap';S=O/'sc';O.mkdir(exist_ok=True)
SK={'node_modules','.git','.codemap','graphify-out','dist','out','__pycache__','vendor','build','bin','obj'}
CE={'.js','.ts','.jsx','.tsx','.mjs','.py','.cs','.cpp','.c','.h','.java','.go','.rb','.php'}
F=[p for p in R.rglob('*') if p.is_file() and not SK&set(p.relative_to(R).parts) and p.suffix.lower() in CE|{'.html','.htm','.gs'} and p.stat().st_size<3e6]
st=hashlib.sha1(''.join(sorted(f'{p}{p.stat().st_mtime_ns}{p.stat().st_size}' for p in F)).encode()).hexdigest()
J=O/'map.json'
if not(J.exists() and json.loads(J.read_text()).get('st')==st):
    from graphify.extract import extract
    S.mkdir(exist_ok=True);[f.unlink() for f in S.glob('*')]
    lm,inp,ids,css,blk,src={},[],{},{},{},{}
    for p in F:
        r=str(p.relative_to(R));t=p.read_text(encoding='utf-8',errors='replace');src[r]=t;s=re.sub(r'\W','_',r);L=lambda k:t.count('\n',0,k)+1
        if p.suffix.lower() in('.html','.htm'):
            for k,m in enumerate(re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',t,re.S)):
                if m.group(1).strip():n=f'{s}_{k}.js';(S/n).write_text(m.group(1));lm[n]=(r,L(m.start(1))-1);inp.append(S/n);blk.setdefault(r,[]).append(L(m.end(1)))
            ids[r]=[(L(m.start()),m.group(1)) for m in re.finditer(r'\bid=\\?["\']([A-Za-z][\w-]*)',t)]
            for m in re.finditer(r'<style[^>]*>(.*?)</style>',t,re.S):
                b=m.start(1)
                for c in re.finditer(r'([^{}@;]+)\{',m.group(1)):
                    sel=' '.join(c.group(1).split())
                    if sel and len(sel)<120:css.setdefault(r,[]).append((L(b+c.start(1)),sel))
        elif p.suffix.lower()=='.gs':n=f'{s}.js';(S/n).write_text(t);lm[n]=(r,0);inp.append(S/n)
        else:inp.append(p)
    res=extract(inp,cache_root=O,root=R) if inp else{'nodes':[],'edges':[]}
    N={n['id']:n for n in res['nodes']};fn={}
    for i,n in N.items():
        l=n.get('label','')
        if not l.endswith('()'):continue
        sf=os.path.basename(n.get('source_file') or '');m=re.fullmatch(r'L(\d+)',n.get('source_location') or '')
        if sf in lm:r,off=lm[sf]
        else:
            try:r=str(Path(n['source_file']).resolve().relative_to(R))
            except Exception:continue
            off=0
        fn[i]=[r,int(m.group(1))+off if m else 0,0,l[:-2],[],[]]
    for e in res['edges']:
        if e.get('relation') in('calls','call','uses') and e['source'] in fn and e['target'] in fn:fn[e['source']][4].append(fn[e['target']][3]);fn[e['target']][5].append(fn[e['source']][3])
    by={}
    for v in fn.values():by.setdefault(v[0],[]).append(v)
    for r,vs in by.items():
        vs.sort(key=lambda v:v[1]);ends=sorted(blk.get(r,[]))+[src[r].count('\n')+1]
        for k,v in enumerate(vs):
            nx=vs[k+1][1] if k+1<len(vs) else 10**9;v[2]=min([nx-1]+[e for e in ends if e>=v[1]])
    J.write_text(json.dumps({'st':st,'fn':{r:[[v[1],v[2],v[3],sorted(set(v[4])),sorted(set(v[5]))] for v in vs] for r,vs in by.items()},'ids':ids,'css':css,'lines':{r:t.count('\n')+1 for r,t in src.items()}},ensure_ascii=False))
M=json.loads(J.read_text())
def row(f):return f'{f[2]} {f[0]}-{f[1]}'+(' >'+','.join(f[3]) if f[3] else '')+(' <'+','.join(f[4]) if f[4] else '')
if not q:
    print('# CODEMAP  nome ini-fim >chama <chamada_por')
    for r in sorted(M['lines']):
        fs=M['fn'].get(r,[]);print(f'## {r} ({M["lines"][r]}L, {len(fs)} fn, {len(M["css"].get(r,[]))} css, {len(M["ids"].get(r,[]))} ids)')
        for f in fs:print(row(f))
    sys.exit()
src={r:(R/r).read_text(encoding='utf-8',errors='replace').split('\n') for r in M['lines']}
for r in sorted(M['lines']):
    out=[];hit=set()
    for f in M['fn'].get(r,[]):
        body='\n'.join(src[r][f[0]-1:f[1]]).lower()
        if any(t in f[2].lower() or t in body for t in q):hit.add(f[2]);out.append(row(f))
    nb=sorted({x for f in M['fn'].get(r,[]) if f[2] in hit for x in f[3]+f[4]}-hit)
    if nb:out.append('  vizinhas: '+'; '.join(f'{f[2]} {f[0]}-{f[1]}' for f in M['fn'][r] if f[2] in nb))
    i=[f'{n}@{l}' for l,n in M['ids'].get(r,[]) if any(t in n.lower() for t in q)]
    if i:out.append('  ids: '+', '.join(i))
    c=[f'{s}@{l}' for l,s in M['css'].get(r,[]) if any(t in s.lower() for t in q)]
    if c:out.append('  css: '+' | '.join(c[:40]))
    tx=[f'{k+1}' for k,ln in enumerate(src[r]) if any(t in ln.lower() for t in q)]
    if tx:out.append(f'  texto nas linhas: {",".join(tx[:60])}'+(' ...' if len(tx)>60 else ''))
    if out:print(f'## {r}');print('\n'.join(out))
