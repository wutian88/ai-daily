"""Exact-date star growth; rankings never fetch the network."""
import calendar,datetime as dt
MAX_REPOS=30
def record(snapshots,day,measurements,candidates):
    cutoff=(dt.date.fromisoformat(day)-dt.timedelta(days=44)).isoformat()
    out={}
    for repo in list(dict.fromkeys(candidates))[:MAX_REPOS]:
        rows={d:n for d,n in snapshots.get(repo,{}).items() if cutoff<=d<=day and isinstance(n,int) and n>=0}
        if repo in measurements:rows[day]=measurements[repo]
        if rows:out[repo]=dict(sorted(rows.items()))
    return out
def change(snapshots,repo,day,days=7,start=None):
    rows=snapshots.get(repo,{})
    start=start or (dt.date.fromisoformat(day)-dt.timedelta(days=days)).isoformat()
    return rows[day]-rows[start] if day in rows and start in rows else None
def label(snapshots,repo,day):
    delta=change(snapshots,repo,day)
    if delta is None:return f'增速数据积累中（已有 {len(snapshots.get(repo,{}))} 天）'
    start=(dt.date.fromisoformat(day)-dt.timedelta(days=7)).isoformat()
    return f'7天星数增长：{delta:+d}（{start} → {day}，按两个日期快照相减）'
def ranking(snapshots,day,period):
    date=dt.date.fromisoformat(day)
    if period=='周':start=(date-dt.timedelta(days=7)).isoformat()
    else:
        # On month day 1 this is previous calendar month's first day.
        prev=date.replace(day=1)-dt.timedelta(days=1)
        start=prev.replace(day=1).isoformat()
    rows=[]
    for repo in snapshots:
        delta=change(snapshots,repo,day,start=start)
        if delta is not None:rows.append((repo,delta))
    rows.sort(key=lambda x:(-x[1],x[0]))
    text=f'{period}榜｜星数增长（{start} → {day}）\n'
    if not rows:return text+'数据不足：缺少起止日期快照，不生成排名。'
    text+='仅对两个日期都有快照的候选仓库排序；不是全网排名。\n'
    return text+'\n'.join(f'{i}. {repo}：{n:+d}' for i,(repo,n) in enumerate(rows[:10],1))
def due_rankings(snapshots,day):
    d=dt.date.fromisoformat(day);out=[]
    if d.weekday()==6:out.append(('周',ranking(snapshots,day,'周')))
    if d.day==1:out.append(('月',ranking(snapshots,day,'月')))
    return out
