
// Custom Function: rruleFromPattern
// Converts simple English like "M/W/F" or "Every Tue" to RRULE string.
String? rruleFromPattern(String text, {String? until}) {
  final t = text.toLowerCase();
  List<String> days = [];
  if (RegExp(r'\bm/?w/?f\b').hasMatch(t)) {
    days = ['MO','WE','FR'];
  } else if (RegExp(r'\bt/?th\b').hasMatch(t)) {
    days = ['TU','TH'];
  } else {
    final map = {
      'mon':'MO','monday':'MO','tue':'TU','tues':'TU','tuesday':'TU',
      'wed':'WE','wednesday':'WE','thu':'TH','thurs':'TH','thursday':'TH',
      'fri':'FR','friday':'FR','sat':'SA','saturday':'SA','sun':'SU','sunday':'SU'
    };
    map.forEach((k,v){
      if (RegExp('\\b'+k+'s?\\b').hasMatch(t)) {
        if (!days.contains(v)) days.add(v);
      }
    });
  }
  if (days.isEmpty) return null;
  final untilStr = (until!=null && until.isNotEmpty)
      ? ';UNTIL=${until.replaceAll(RegExp(r'[-:]'), '')}Z' : '';
  return 'RRULE:FREQ=WEEKLY;BYDAY=${days.join(',')}$untilStr';
}
