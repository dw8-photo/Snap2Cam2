
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import re

app = FastAPI(title="Snap2Schedule Parse API", version="0.1.0")

class SemesterWindow(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class ParseRequest(BaseModel):
    text: str
    timezone: str = "America/Detroit"
    default_year: int = datetime.now().year
    semester_window: Optional[SemesterWindow] = None

class EventOut(BaseModel):
    title: str
    start_iso: str
    end_iso: Optional[str] = None
    all_day: bool = False
    recurrence_rule: Optional[str] = None
    labels: List[str] = []
    location: str = ""
    notes: str = ""
    confidence: float = 0.85

class ParseResponse(BaseModel):
    events: List[EventOut]
    warnings: List[str] = []

MONTHS = {'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,
    'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,
    'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}

DAY_ABBR = {'mon':'MO','tue':'TU','tues':'TU','wed':'WE','thu':'TH','thurs':'TH','fri':'FR','sat':'SA','sun':'SU'}

LABELS = [
    (r'\b(no school|holiday)\b', 'No School'),
    (r'\b(half[-\s]?day|early release)\b', 'Half Day'),
    (r'\b(midterm|finals?|exam)\b', 'Exam'),
    (r'\bquiz\b', 'Quiz'),
    (r'\bparent[-\s]?teacher conference\b', 'Parent-Teacher Conference'),
    (r'\b(assignment|project)\s+due\b', 'Due'),
]

def detect_labels(line: str):
    labs = set()
    for patt, lab in LABELS:
        if re.search(patt, line, re.I): labs.add(lab)
    return list(labs) or ["Other"]

def parse_date(tok: str, year: int):
    tok = tok.strip()
    m = re.match(r'(?P<m>\d{1,2})/(?P<d>\d{1,2})', tok)
    if m: return datetime(year, int(m.group('m')), int(m.group('d')))
    m = re.match(r'(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2})', tok)
    if m:
        mon = m.group('mon').lower()
        month = MONTHS.get(mon[:3], MONTHS.get(mon))
        if month: return datetime(year, month, int(m.group('d')))
    return None

def parse_time_range(tok: str):
    t = tok.lower().replace(" ","")
    m = re.match(r'(\d{1,2}(:\d{2})?)(am|pm)?[–\-](\d{1,2}(:\d{2})?)(am|pm)?', t)
    if m: return (m.group(1)+(m.group(3) or ''), m.group(4)+(m.group(6) or ''))
    m = re.match(r'(\d{1,2}(:\d{2})?)(am|pm)$', t)
    if m: return (m.group(1)+m.group(3), None)
    return None

def to_24h(tstr: str):
    ampm = 'am' if tstr.endswith('am') else ('pm' if tstr.endswith('pm') else None)
    t = tstr.replace('am','').replace('pm','')
    h,m = (t.split(':')+[0])[:2]
    h = int(h); m = int(m) if isinstance(m,str) else 0
    if ampm == 'pm' and h != 12: h += 12
    if ampm == 'am' and h == 12: h = 0
    return h,m

def infer_end(start_dt, end_tok):
    if end_tok:
        eh,em = to_24h(end_tok)
        end_dt = start_dt.replace(hour=eh, minute=em)
        if end_dt <= start_dt: end_dt += timedelta(hours=1)
        return end_dt
    return start_dt + timedelta(minutes=45)

def parse_rrule(line: str):
    days = []
    if re.search(r'\bm/?w/?f\b', line, re.I): days = ['MO','WE','FR']
    elif re.search(r'\bt/?th\b', line, re.I): days = ['TU','TH']
    else:
        for k,v in DAY_ABBR.items():
            if re.search(r'\b'+k+r's?\b', line, re.I): days.append(v)
        days = sorted(set(days))
    return f"RRULE:FREQ=WEEKLY;BYDAY={','.join(days)}" if days else None

@app.post("/parse_events", response_model=ParseResponse)
def parse_events(req: ParseRequest):
    text = req.text
    events = []
    warnings = []
    lines = [l.strip() for l in re.split(r'[\n;]+', text) if l.strip()]
    for line in lines:
        labels = detect_labels(line)
        dr = re.search(r'([A-Za-z]{3,9}\s+\d{1,2})\s*[–-]\s*(\d{1,2})', line)  # Dec 16–20
        dm = re.search(r'((?:\d{1,2}/\d{1,2})|(?:[A-Za-z]{3,9}\s+\d{1,2}))', line)
        tm = re.search(r'(\d{1,2}(:\d{2})?\s*(am|pm)?\s*[–-]\s*\d{1,2}(:\d{2})?\s*(am|pm)?)', line, re.I)
        st = re.search(r'(\d{1,2}(:\d{2})?\s*(am|pm))', line, re.I)

        if dr:
            start_tok = dr.group(1)
            end_day = int(dr.group(2))
            start_dt = parse_date(start_tok, req.default_year)
            if start_dt:
                end_dt = start_dt.replace(day=end_day) + timedelta(days=1)
                events.append(EventOut(title=line.split(':')[0][:80] if ':' in line else line[:80],
                    start_iso=start_dt.replace(hour=0, minute=0).isoformat(),
                    end_iso=end_dt.replace(hour=0, minute=0).isoformat(),
                    all_day=True, recurrence_rule=None, labels=labels, confidence=0.80))
                continue

        if dm:
            d = parse_date(dm.group(1), req.default_year)
            if d:
                if tm:
                    s,e = parse_time_range(tm.group(1))
                    sh,sm = to_24h(s)
                    start_dt = d.replace(hour=sh, minute=sm)
                    end_dt = infer_end(start_dt, e)
                    events.append(EventOut(title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=start_dt.isoformat(), end_iso=end_dt.isoformat(), all_day=False,
                        recurrence_rule=parse_rrule(line), labels=labels, confidence=0.88))
                elif st:
                    s,_ = parse_time_range(st.group(1)) or (st.group(1), None)
                    sh,sm = to_24h(s)
                    start_dt = d.replace(hour=sh, minute=sm)
                    end_dt = infer_end(start_dt, None)
                    events.append(EventOut(title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=start_dt.isoformat(), end_iso=end_dt.isoformat(), all_day=False,
                        recurrence_rule=parse_rrule(line), labels=labels, confidence=0.83))
                else:
                    events.append(EventOut(title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=d.replace(hour=0, minute=0).isoformat(),
                        end_iso=(d+timedelta(days=1)).replace(hour=0, minute=0).isoformat(),
                        all_day=True, recurrence_rule=parse_rrule(line), labels=labels, confidence=0.86))
            else:
                warnings.append(f"Ambiguous date: {line}")
        else:
            if re.search(r'week of|finals week|tba', line, re.I):
                warnings.append(f"Ambiguous timeframe: {line}")

    return ParseResponse(events=events, warnings=warnings)
