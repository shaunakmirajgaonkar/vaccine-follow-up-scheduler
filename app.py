from pathlib import Path
from datetime import date
import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='VaxFollow Local',page_icon='💉',layout='wide',initial_sidebar_state='expanded')
REQUIRED=['record_id','person_code','age_band','dose_name','vaccine_group','due_date','administered_date','status','reminder_status','preferred_language','care_setting','follow_up_contact_available','high_priority_flag','notes']
DEFAULT=Path('data/vaccine_follow_up_registry.csv')
st.markdown('''<style>
.stApp{background:linear-gradient(180deg,#f8fbfc,#f1f6f7);color:#16242c}.block-container{max-width:1450px;padding-top:1.3rem}section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #dfe8ec}section[data-testid="stSidebar"] *{color:#16242c!important}.hero{background:linear-gradient(135deg,#fff,#eaf7f4);border:1px solid #dbe7eb;border-radius:24px;padding:28px 32px;box-shadow:0 8px 28px #18333d0d}.hero h1{margin:5px 0;color:#14232d;font-size:2.35rem}.eyebrow{color:#176b87;font-size:.78rem;font-weight:800;letter-spacing:.13em}.pill{display:inline-block;padding:7px 11px;margin:5px 6px 0 0;border-radius:999px;background:#fff;border:1px solid #d7e4e8;color:#31505b;font-size:.78rem;font-weight:700}.notice{background:#fffaf0;border:1px solid #ead9ac;color:#5f4d25;border-radius:16px;padding:15px 18px}.card{background:#fff;border:1px solid #dfe8ec;border-radius:20px;padding:20px;box-shadow:0 5px 18px #18333d08}.metric{background:#fff;border:1px solid #dfe8ec;border-radius:18px;padding:17px;min-height:100px}.metric .l{color:#687781;font-size:.78rem;font-weight:700}.metric .v{color:#14232d;font-size:1.75rem;font-weight:850;margin-top:4px}.queue{background:#fff;border:1px solid #dfe8ec;border-left:5px solid #2b8a78;border-radius:15px;padding:14px 16px;margin:8px 0}.small{color:#687781;font-size:.82rem}
</style>''',unsafe_allow_html=True)

def load(up): return pd.read_csv(io.BytesIO(up.getvalue())) if up else pd.read_csv(DEFAULT)
def validate(df):
    m=[c for c in REQUIRED if c not in df.columns]
    if m:return False,'Missing required columns: '+', '.join(m)
    if df.record_id.isna().any():return False,'record_id contains missing values.'
    if df.record_id.duplicated().any():return False,'record_id contains duplicates.'
    return True,'Dataset structure is valid.'
def enrich(df,review):
    out=df.copy(); scores=[]; levels=[]; reasons=[]; days=[]
    for _,r in out.iterrows():
        status=str(r.status).lower().strip(); reminder=str(r.reminder_status).lower().strip(); s=0; rs=[]
        if status=='missed':s+=30;rs.append('Marked missed in local registry')
        elif status=='delayed':s+=25;rs.append('Marked delayed in local registry')
        elif status=='due':s+=12;rs.append('Marked due in local registry')
        due=pd.to_datetime(r.due_date,errors='coerce')
        d=max(0,(pd.Timestamp(review)-due.normalize()).days) if pd.notna(due) and status not in {'completed','cancelled'} else 0
        if d>0:
            p=min(20,round(d/3));s+=p;rs.append(f'{d} day(s) past supplied due date')
        if str(r.follow_up_contact_available).lower().strip() in {'no','false','0'}:s+=10;rs.append('No follow-up contact channel marked available')
        if str(r.high_priority_flag).lower().strip() in {'yes','true','1'}:s+=10;rs.append('Locally flagged for higher-priority follow-up')
        if reminder in {'pending','not_sent','not contacted'}:s+=5;rs.append('Follow-up reminder remains pending')
        s=min(100,int(s)); level='Urgent Review' if s>=75 else 'High Priority' if s>=50 else 'Attention' if s>=25 else 'Routine'
        scores.append(s);levels.append(level);reasons.append(' • '.join(rs) or 'No priority signals detected');days.append(d)
    out['follow_up_score']=scores;out['priority_class']=levels;out['explanation']=reasons;out['days_since_due']=days
    return out
with st.sidebar:
    st.markdown('### 💉 VaxFollow Local');st.caption('Privacy-conscious follow-up workspace');st.divider();review=st.date_input('Review date',date.today());up=st.file_uploader('Replace local registry',type=['csv']);st.divider();st.write('**100% local processing**');st.write('No external APIs');st.write('Synthetic / authorized records only')
df=load(up);ok,msg=validate(df)
if not ok:st.error(msg);st.stop()
df=enrich(df,review)
st.markdown('''<div class="hero"><div class="eyebrow">LOCAL-FIRST · HUMAN REVIEW · EXPLAINABLE</div><h1>💉 VaxFollow Local</h1><p><b>Vaccine Follow-Up Scheduler</b> — organize locally supplied dose dates, identify missed or delayed records, and prepare privacy-conscious human follow-up queues.</p><span class="pill">100% Local Processing</span><span class="pill">No External APIs</span><span class="pill">Transparent Rules</span><span class="pill">Human Review</span></div>''',unsafe_allow_html=True)
st.markdown('<div class="notice"><b>Clinical safety boundary:</b> This workspace does not prescribe vaccines or generate an authoritative catch-up schedule. It screens only the dates/statuses supplied in the local registry. Confirm current official guidance and any catch-up action with an appropriately qualified healthcare professional.</div>',unsafe_allow_html=True)
total=len(df);completed=int((df.status.str.lower()=='completed').sum());queue=int(df.priority_class.isin(['Attention','High Priority','Urgent Review']).sum());urgent=int((df.priority_class=='Urgent Review').sum())
cs=st.columns(4)
for c,l,v in zip(cs,['LOCAL RECORDS','COMPLETED','FOLLOW-UP QUEUE','URGENT REVIEW'],[total,completed,queue,urgent]):c.markdown(f'<div class="metric"><div class="l">{l}</div><div class="v">{v}</div></div>',unsafe_allow_html=True)
st.write('')
t1,t2,t3,t4,t5=st.tabs(['Overview','Follow-up Queue','Dose Explorer','Analytics','Data Lab'])
with t1:
    a,b=st.columns([1.15,.85])
    with a:
        st.markdown('<div class="card"><h3>Follow-up landscape</h3><p class="small">Local operational status overview.</p>',unsafe_allow_html=True)
        x=df.status.astype(str).str.title().value_counts().reset_index();x.columns=['Status','Records'];fig=px.bar(x,x='Status',y='Records',text='Records');fig.update_layout(template='plotly_white',height=350,margin=dict(l=10,r=10,t=10,b=10));st.plotly_chart(fig,use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><h3>Priority distribution</h3><p class="small">Transparent operational screening classes.</p>',unsafe_allow_html=True)
        x=df.priority_class.value_counts().reindex(['Routine','Attention','High Priority','Urgent Review']).fillna(0).reset_index();x.columns=['Priority','Records'];fig=px.pie(x,names='Priority',values='Records',hole=.58);fig.update_layout(template='plotly_white',height=350,margin=dict(l=10,r=10,t=10,b=10));st.plotly_chart(fig,use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('### Highest-priority local records')
    for _,r in df.sort_values(['follow_up_score','days_since_due'],ascending=False).head(5).iterrows():
        st.markdown(f'<div class="queue"><b>{r.record_id} · {r.dose_name}</b><span style="float:right"><b>{r.follow_up_score}/100</b> · {r.priority_class}</span><br><span class="small">Due: {r.due_date} · Status: {r.status} · Language: {r.preferred_language} · Setting: {r.care_setting}</span></div>',unsafe_allow_html=True)
with t2:
    st.markdown('### Human follow-up queue');classes=st.multiselect('Priority classes',['Routine','Attention','High Priority','Urgent Review'],['Attention','High Priority','Urgent Review']);q=df[df.priority_class.isin(classes)].sort_values(['follow_up_score','days_since_due'],ascending=False);st.write(f'**{len(q)} records** in selected queue.');st.dataframe(q[['record_id','person_code','dose_name','due_date','status','days_since_due','follow_up_score','priority_class','reminder_status','follow_up_contact_available','preferred_language','explanation']],use_container_width=True,hide_index=True);st.download_button('Download follow-up queue CSV',q.to_csv(index=False).encode(),'vaxfollow_follow_up_queue.csv','text/csv')
with t3:
    st.markdown('### Dose-level explorer');sel=st.selectbox('Select record',df.record_id.tolist());r=df[df.record_id==sel].iloc[0];a,b,c=st.columns(3);a.metric('Follow-up score',f"{r.follow_up_score}/100");b.metric('Priority',r.priority_class);c.metric('Days since supplied due date',int(r.days_since_due));st.markdown('#### Local record');st.dataframe(pd.DataFrame([r]),use_container_width=True,hide_index=True);st.markdown('#### Explainable factors');st.info(r.explanation);st.markdown('#### Operational next step');st.write('Route the record to the appropriate human follow-up workflow and verify current official guidance before any clinical action.')
with t4:
    st.markdown('### Analytics');a,b=st.columns(2)
    with a:
        x=df.groupby('preferred_language').size().reset_index(name='records');fig=px.bar(x,x='preferred_language',y='records',text='records',title='Records by preferred language');fig.update_layout(template='plotly_white',height=330);st.plotly_chart(fig,use_container_width=True)
    with b:
        x=df.groupby('care_setting').size().reset_index(name='records');fig=px.bar(x,x='care_setting',y='records',text='records',title='Records by care setting');fig.update_layout(template='plotly_white',height=330);st.plotly_chart(fig,use_container_width=True)
    fig=px.histogram(df,x='follow_up_score',nbins=10,title='Follow-up screening score distribution');fig.update_layout(template='plotly_white',height=330);st.plotly_chart(fig,use_container_width=True)
with t5:
    st.markdown('### Local Data Lab');st.write('CSV files are validated and processed entirely on this machine.');st.code(', '.join(REQUIRED));st.success(msg);st.write(f'**Current dataset:** {len(df)} records × {len(df.columns)} columns');st.dataframe(df,use_container_width=True,hide_index=True);st.download_button('Download scored local registry',df.to_csv(index=False).encode(),'vaxfollow_scored_registry.csv','text/csv')
