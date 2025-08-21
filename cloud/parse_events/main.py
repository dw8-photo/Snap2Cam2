
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os, re, json

app = FastAPI(title="Snap2Schedule Parse API", version="0.1.0")

# --- Models ---
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

# --- Helpers ---
MONTHS = {
    'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,
    'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,
    'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12
}
DAY_ABBR = {'m': 'MO','mon':'MO','t':'TU','tu':'TU','tue':'TU','tues':'TU','w':'WE','wed':'WE',
            'th':'TH','thu':'TH','thur':'TH','thurs':'TH','f':'FR','fri':'FR','sa':'SA','sat':'SA','su':'SU','sun':'SU'}

LABEL_PATTERNS = [
    (r'\b(no school|holiday)\b', 'No School'),
    (r'\b(half[-\s]?day|early release)\b', 'Half Day'),
    (r'\b(midterm|finals?|exam)\b', 'Exam'),
    (r'\b(quiz)\b', 'Quiz'),
    (r'\b(parent[-\s]?teacher conference)\b', 'Parent-Teacher Conference'),
    (r'\b(assignment|project)\s+(due)\b', 'Due'),
]

def load_keywords() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "keywords.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def detect_labels(text: str) -> List[str]:
    labels = set()
    for patt, label in LABEL_PATTERNS:
        if re.search(patt, text, flags=re.I):
            labels.add(label)
    return list(labels) or ["Other"]

def parse_date_tokens(tok: str, year: int) -> Optional[datetime]:
    tok = tok.strip()
    # Examples: 9/18, 09/01, Sept 1, Oct 14, Dec 16–20
    m = re.match(r'(?P<m>\d{1,2})/(?P<d>\d{1,2})', tok)
    if m:
        month = int(m.group('m'))
        day = int(m.group('d'))
        return datetime(year, month, day)
    m = re.match(r'(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2})', tok)
    if m:
        mon = m.group('mon').lower()
        day = int(m.group('d'))
        month = MONTHS.get(mon[:3], MONTHS.get(mon, None))
        if month:
            return datetime(year, month, day)
    return None

def parse_time_range(tok: str) -> Optional[tuple]:
    # Examples: 10–11:30am, 5–8 PM, 1:30pm, 10am-11am
    tok = tok.lower().replace(" ", "")
    m = re.match(r'(?P<s>\d{1,2}(:\d{2})?)(?P<sampm>am|pm)?[–\-](?P<e>\d{1,2}(:\d{2})?)(?P<eampm>am|pm)?', tok)
    if m:
        return (m.group('s') + (m.group('sampm') or ''), m.group('e') + (m.group('eampm') or ''))
    m = re.match(r'(?P<s>\d{1,2}(:\d{2})?)(?P<ampm>am|pm)$', tok)
    if m:
        return (m.group('s') + m.group('ampm'), None)
    return None

def to_24h(tstr: str) -> tuple:
    # returns (hour, minute)
    ampm = 'am' if tstr.endswith('am') else ('pm' if tstr.endswith('pm') else None)
    t = tstr.replace('am','').replace('pm','')
    if ':' in t:
        h, mi = t.split(':')
        h = int(h); mi = int(mi)
    else:
        h = int(t); mi = 0
    if ampm == 'pm' and h != 12: h += 12
    if ampm == 'am' and h == 12: h = 0
    return h, mi

def infer_end(start_dt: datetime, end_tok: Optional[str]) -> datetime:
    if end_tok:
        eh, em = to_24h(end_tok)
        end_dt = start_dt.replace(hour=eh, minute=em)
        if end_dt <= start_dt:
            end_dt += timedelta(hours=1)
        return end_dt
    return start_dt + timedelta(minutes=45)

def parse_rrule(line: str, until: Optional[str]) -> Optional[str]:
    # Very lightweight patterns: "M/W/F", "Every Tue", "TTh", "Weekly on Tuesdays"
    days = []
    if re.search(r'\bm/?w/?f\b', line, re.I): days = ['MO','WE','FR']
    elif re.search(r'\bt/?th\b', line, re.I): days = ['TU','TH']
    else:
        found = []
        for k,v in DAY_ABBR.items():
            if re.search(r'\b'+re.escape(k)+r's?\b', line, re.I): found.append(v)
        days = sorted(set(found))
    if days:
        until_str = ""
        if until:
            # UNTIL must be in UTC-like ical dtstamp (just append Z naive)
            until_str = f";UNTIL={until.replace('-','').replace(':','')}Z"
        return f"RRULE:FREQ=WEEKLY;BYDAY={','.join(days)}{until_str}"
    return None

# --- (Optional) LLM stub ---
def llm_parse(text: str, tz: str, year: int, window: Optional[SemesterWindow]) -> List[EventOut]:
    """Placeholder for LLM; returns empty to let regex fallback handle most cases.
    You can integrate any LLM here and merge results.
    """
    return []

# --- Core parse ---
@app.post("/parse_events", response_model=ParseResponse)
def parse_events(req: ParseRequest):
    text = req.text
    warnings = []
    events: List[EventOut] = []

    # Try LLM first (stubbed — returns [] by default)
    events += llm_parse(text, req.timezone, req.default_year, req.semester_window)

    # Regex fallback heuristics
    lines = [l.strip() for l in re.split(r'[\n;]+', text) if l.strip()]
    for line in lines:
        labels = detect_labels(line)
        # Date tokens
        date_match = re.search(r'((?:\d{1,2}/\d{1,2})|(?:[A-Za-z]{3,9}\s+\d{1,2}))', line)
        daterange_match = re.search(r'([A-Za-z]{3,9}\s+\d{1,2})\s*[–-]\s*(\d{1,2})', line)  # Dec 16–20
        time_match = re.search(r'(\d{1,2}(:\d{2})?\s*(?:am|pm)?\s*[–-]\s*\d{1,2}(:\d{2})?\s*(?:am|pm)?)', line, re.I)
        single_time_match = re.search(r'(\d{1,2}(:\d{2})?\s*(am|pm))', line, re.I)

        if daterange_match:
            start_tok = daterange_match.group(1)
            end_day = int(daterange_match.group(2))
            start_dt = parse_date_tokens(start_tok, req.default_year)
            if start_dt:
                end_dt = start_dt.replace(day=end_day) + timedelta(days=1)
                events.append(EventOut(
                    title=line.split(':')[0][:80] if ':' in line else line[:80],
                    start_iso=start_dt.replace(hour=0, minute=0).isoformat(),
                    end_iso=end_dt.replace(hour=0, minute=0).isoformat(),
                    all_day=True,
                    recurrence_rule=None,
                    labels=labels,
                    confidence=0.80
                ))
                continue

        if date_match:
            dt = parse_date_tokens(date_match.group(1), req.default_year)
            if dt:
                if time_match:
                    st, et = parse_time_range(time_match.group(1))
                    sh, sm = to_24h(st)
                    start_dt = dt.replace(hour=sh, minute=sm)
                    end_dt = infer_end(start_dt, et)
                    events.append(EventOut(
                        title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=start_dt.isoformat(),
                        end_iso=end_dt.isoformat(),
                        all_day=False,
                        recurrence_rule=parse_rrule(line, None),
                        labels=labels,
                        confidence=0.88
                    ))
                elif single_time_match:
                    st = single_time_match.group(1).replace(" ", "")
                    sh, sm = to_24h(st.lower())
                    start_dt = dt.replace(hour=sh, minute=sm)
                    end_dt = infer_end(start_dt, None)
                    events.append(EventOut(
                        title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=start_dt.isoformat(),
                        end_iso=end_dt.isoformat(),
                        all_day=False,
                        recurrence_rule=parse_rrule(line, None),
                        labels=labels,
                        confidence=0.83
                    ))
                else:
                    # All-day
                    events.append(EventOut(
                        title=line.split(':')[0][:80] if ':' in line else line[:80],
                        start_iso=dt.replace(hour=0, minute=0).isoformat(),
                        end_iso=(dt + timedelta(days=1)).replace(hour=0, minute=0).isoformat(),
                        all_day=True,
                        recurrence_rule=parse_rrule(line, None),
                        labels=labels,
                        confidence=0.86
                    ))
            else:
                warnings.append(f"Ambiguous date in line: {line}")
        else:
            if re.search(r'week of|finals week|tba', line, re.I):
                warnings.append(f"Ambiguous timeframe: {line}")

    return ParseResponse(events=events, warnings=warnings)
