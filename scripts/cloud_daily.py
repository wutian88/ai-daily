"""Cloud source digest. Standard library only; no LLM or paid API."""
import argparse, datetime as dt, hashlib, html, json, os, re, sys, time
import urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from trends import record, label, due_rankings, change
TZ=dt.timezone(dt.timedelta(hours=8))
ROOT=Path(__file__).resolve().parents[1]
REPOS=['langgenius/dify','langflow-ai/langflow','mem0ai/mem0','promptfoo/promptfoo','huggingface/trl','pgvector/pgvector','NVIDIA-AI-Blueprints/data-flywheel']
FEEDS=[('官方博客','https://huggingface.co/blog/feed.xml'),('论文','https://rss.arxiv.org/rss/cs.AI')]
ADVICE={
 'langgenius/dify':('Agent工作流','将任务拆为检索、工具调用和回答，分别设置输入输出契约。','以20条固定问题比较改动前后任务完成率、延迟和错误类型。'),
 'langflow-ai/langflow':('Agent编排','可视化工作流将数据与模型调用连成可观察的链。','只在隔离环境复现一个只读流程，记录输入、每步输出及失败边界。'),
 'mem0ai/mem0':('长期记忆','外部事实存储和按需检索减少全历史重放，但引入过期和错配风险。','用事实更新、跨用户隔离、细节回忆三类案例对照全历史与外部记忆。'),
 'promptfoo/promptfoo':('评测','固定用例与断言用于检查提示词或模型改动是否回归。','准备正常、边界、拒答案例；冻结测试集，逐例记录回归而非只看平均分。'),
 'huggingface/trl':('强化学习与后训练','奖励或偏好信号改变训练目标；奖励质量影响是否学会投机。','先阅读版本差异；保持数据、模型和评测相同再比较，不自动训练。'),
 'pgvector/pgvector':('RAG检索','向量相似度帮助候选召回，业务语义与证据正确性仍须另行评测。','比较关键词与向量Recall@5，再分别核对引用和生成答案，不混成一个分数。'),
 'NVIDIA-AI-Blueprints/data-flywheel':('数据飞轮','生产轨迹经过筛选、标注、评测与优化形成迭代闭环。','按失败类型构建开发集与独立留出集；先验证数据质量，再考虑蒸馏。')}
def fetch(url,token=None):
    headers={'User-Agent':'AI-Study-Daily/1.0','Accept':'application/json' if 'api.github.com' in url else '*/*'}
    if token and url.startswith('https://api.github.com/'):headers['Authorization']='Bearer '+token
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25) as r:
                b=r.read(4_000_001)
                if len(b)>4_000_000:raise ValueError('source exceeds size limit')
                return b
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def feed_rows(raw,kind,source):
    root=ET.fromstring(raw); rows=[]
    for e in root.findall('.//item'):
        title=plain(e.findtext('title'));url=(e.findtext('link') or '').strip()
        if not title or not url.startswith('https://'):continue
        if kind in ['官方博客','论文'] and not any(x in (title+' '+e.findtext('description','')).lower() for x in ['agent','ai ','gemini','model','llm','rag','retrieval','memory','reasoning','reinforcement','distill']):continue
        published=e.findtext('pubDate','')
        try:
            stamp=parsedate_to_datetime(published)
            if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=dt.timezone.utc)
            age=dt.datetime.now(TZ)-stamp
            if age<dt.timedelta(days=-1) or age>dt.timedelta(days=30):continue
        except (ValueError,TypeError):continue
        rows.append({'kind':kind,'title':title,'url':url,'published':published,'summary':plain(e.findtext('description',''))[:500],'source':source,'timestamp':stamp.timestamp()})
    return sorted(rows,key=lambda x:x['timestamp'],reverse=True)
def generate_body(day,chosen,gaps,snapshots=None):
    snapshots=snapshots or {}
    lines=[f'# AI来源简报｜{day}','', '生成方式：GitHub Actions 云端结构化抓取；未调用模型，非Claude逐日撰写。正文摘要为自动截取，实践建议为维护者预设模板，不是对新版本效果的验证。','',f'检索日期：{day}（北京时间）。选题按来源新鲜度和轮换规则，不是全网热度榜。','']
    for i,x in enumerate(chosen,1):
        lines += [f"## {i}. {x['title']}",'','### 来源陈述',f"来源类型：{x['kind']}；原始时间：{x['published']}。",f"链接：{x['url']}"]
        if x['kind']=='GitHub':
            theory,principle,practice=ADVICE.get(x['repo'],('新项目','项目的机制与适用场景需阅读README和示例核实。','先检查许可证、依赖与示例，再用固定输入验证，不自动执行陌生代码。'))
            lines += [f"累计stars：{x['stars']}（本次快照，不是今日增星）。", ('新项目热度：近30天新建AI主题项目，按累计星数筛选，不代表增速。' if x.get('new_project') else label(snapshots,x['repo'],day)),f"关注问题：{theory}如何可靠落地？",'','### 我的推断与实践建议',f'原理：{principle}',f'实践：{practice}']
        else:
            if x['kind']=='论文':lines += ['论文按订阅源发表/公告日期和主题筛选，不排热度；预印本，效果只属作者报告，未独立复现。']
            lines += ['自动截取的来源摘要（可能截断）：',x['summary'] or '来源无摘要，请阅读原文。','','### 我的推断与实践建议','问题：这项方法解决的瓶颈是否也存在于你的任务？','原理：请按原文核对模型、数据、目标与约束；此程序不推断论文机制。','实践：列出原文基线与变量，先做一个最小对照；记录输入、成功标准、延迟和成本。']
        lines+=['','### 结果与限制','本地/云端模型实验：未实测。抓取成功不代表方法有效；作者效果须回到原文核对，不由此程序生成提升数字。','','---','']
    if gaps:lines+=['## 来源缺口']+[f'- {g}' for g in gaps]
    return '\n'.join(lines)+'\n'
def update(root,day,chosen,gaps,snapshots=None):
    content=root/'public/ai-daily/content.json'
    data=json.loads(content.read_text(encoding='utf-8'))
    item={'id':'cloud-'+day,'kind':'日报','title':f'AI来源简报｜{day}','body':generate_body(day,chosen,gaps,snapshots)}
    summaries=[{'id':f'rank-{period}-{day}','kind':'日报','title':f'{period}榜｜{day}','body':'# '+text} for period,text in due_rankings(snapshots or {},day)]
    summary_ids={x['id'] for x in summaries}
    data['items']=[x for x in data['items'] if x['id'] not in summary_ids]
    data['items']=summaries+[item]+[x for x in data['items'] if x['id']!=item['id']]
    data['updated']=day
    encoded=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    # Validate before any output. Source failures never replace this file.
    assert len(chosen)>=2 and len(set(x['kind'] for x in chosen))>=2
    assert all(x['url'].startswith('https://') for x in chosen)
    json.loads(encoded)
    paths={content:encoded,root/f'ai-daily/archive/{day}.md':item['body'],root/'ai-daily/state.json':json.dumps({'date':day,'schema':2,'seen': [x['url'] for x in chosen]},ensure_ascii=False,indent=2)+'\n'}
    if snapshots is not None:paths[root/'public/ai-daily/snapshots.json']=json.dumps(snapshots,ensure_ascii=False,indent=2)+'\n'
    for summary in summaries:paths[root/f"ai-daily/archive/{summary['id']}.md"]=summary['body']+'\n'
    oldstate=root/'ai-daily/state.json'
    if oldstate.exists():
        prev=json.loads(oldstate.read_text(encoding='utf-8')); state=json.loads(paths[oldstate]);state['seen']=list(dict.fromkeys(prev.get('seen',[])+state['seen']))[-2000:];paths[oldstate]=json.dumps(state,ensure_ascii=False,indent=2)+'\n'
    for p,s in paths.items():p.parent.mkdir(parents=True,exist_ok=True);p.with_suffix(p.suffix+'.tmp').write_text(s,encoding='utf-8')
    for p in paths:p.with_suffix(p.suffix+'.tmp').replace(p)
    print(json.dumps({'date':day,'selected':len(chosen),'kinds':sorted(set(x['kind'] for x in chosen)),'gaps':gaps},ensure_ascii=True))
def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);args=a.parse_args();root=args.root
    today=dt.datetime.now(TZ);day=today.date().isoformat();statefile=root/'ai-daily/state.json'
    state=json.loads(statefile.read_text(encoding='utf-8')) if statefile.exists() else {}
    if state.get('date')==day and state.get('schema')==2:print('Already generated today; no rewrite');return
    seen=set(state.get('seen',[]));token=os.environ.get('GH_TOKEN');gaps=[];measurements={};repo_rows=[]
    cutoff=(today.date()-dt.timedelta(days=30)).isoformat()
    query=urlencode({'q':f'topic:artificial-intelligence created:>={cutoff} archived:false','sort':'stars','order':'desc','per_page':23})
    new=[]
    try:new=json.loads(fetch('https://api.github.com/search/repositories?'+query,token))['items']
    except Exception as e:gaps.append('新项目搜索：'+type(e).__name__)
    candidates=list(dict.fromkeys(REPOS+[x['full_name'] for x in new]))[:30]
    for repo in REPOS:
        try:
            d=json.loads(fetch('https://api.github.com/repos/'+repo,token));measurements[repo]=d['stargazers_count']
            repo_rows.append({'kind':'GitHub','repo':repo,'title':repo+' 星数观察','url':d['html_url'],'published':day+' 快照','stars':d['stargazers_count']})
        except Exception as e:gaps.append(repo+'：'+type(e).__name__)
    for d in new:
        if d['full_name'] not in candidates:continue
        measurements[d['full_name']]=d['stargazers_count']
    sf=root/'public/ai-daily/snapshots.json'
    previous=json.loads(sf.read_text(encoding='utf-8')) if sf.exists() else {}
    snapshots=record(previous,day,measurements,candidates)
    # Compute changes from exact dated snapshots; never substitute cumulative stars.
    repo_rows.sort(key=lambda x:(change(snapshots,x['repo'],day) is not None,change(snapshots,x['repo'],day) or 0),reverse=True)
    chosen=repo_rows[:1]
    if new:
        d=new[0];chosen.append({'kind':'GitHub','repo':d['full_name'],'title':d['full_name']+'｜新项目热度','url':d['html_url'],'published':d['created_at'],'stars':d['stargazers_count'],'new_project':True})
    feeds=[]
    for kind,url in FEEDS:
        try:feeds.extend(x for x in feed_rows(fetch(url),kind,url) if x['url'] not in seen)
        except Exception as e:gaps.append(kind+'：'+type(e).__name__)
    for kind,_ in FEEDS:
        row=next((x for x in feeds if x['kind']==kind),None)
        if row:chosen.append(row)
    if len(chosen)<2 or len({x['kind'] for x in chosen})<2:raise RuntimeError('Insufficient sources; retain previous content. '+repr(gaps))
    update(root,day,chosen[:4],gaps,snapshots)
if __name__=='__main__':main()
