
// Custom Function: normalizeTimespan
// Input examples: "10–11:30am", "5–8 PM", "1:30pm", "10am-11am"
Map<String, String?> normalizeTimespan(String text) {
  final t = text.toLowerCase().replaceAll(' ', '');
  final range = RegExp(r'(?:(\d{1,2}(:\d{2})?)(am|pm)?)[–-](\d{1,2}(:\d{2})?)(am|pm)?');
  final single = RegExp(r'(\d{1,2}(:\d{2})?)(am|pm)$');
  String? s, e;
  final rm = range.firstMatch(t);
  if (rm != null) {
    s = (rm.group(1) ?? '') + (rm.group(3) ?? '');
    e = (rm.group(4) ?? '') + (rm.group(6) ?? '');
  } else {
    final sm = single.firstMatch(t);
    if (sm != null) {
      s = (sm.group(1) ?? '') + (sm.group(3) ?? '');
      e = null;
    }
  }
  return {'start': s, 'end': e};
}
