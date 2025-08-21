
// Custom Action: BuildICSFile
// Generates a minimal .ics string for a single event (extend for batches).
// Use share_plus to share the file.
import 'dart:io';
import 'package:path_provider/path_provider.dart';

Future<String> buildICSFile({
  required String uid,
  required String title,
  required DateTime start,
  required DateTime end,
  bool allDay = false,
  String? location,
  String? notes,
  String? rrule, // full ICAL RRULE e.g. "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"
}) async {
  String dt(DateTime d) =>
      d.toUtc().toIso8601String().replaceAll('-', '').replaceAll(':', '').split('.').first + 'Z';

  final lines = <String>[
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Snap2Schedule//EN',
    'BEGIN:VEVENT',
    'UID:$uid',
    'DTSTAMP:${dt(DateTime.now())}',
    'SUMMARY:${title.replaceAll('\n', ' ')}',
    allDay ? 'DTSTART;VALUE=DATE:${start.toUtc().toIso8601String().split("T")[0].replaceAll("-", "")}'
           : 'DTSTART:${dt(start)}',
    allDay ? 'DTEND;VALUE=DATE:${end.toUtc().toIso8601String().split("T")[0].replaceAll("-", "")}'
           : 'DTEND:${dt(end)}',
  ];
  if (location != null && location.isNotEmpty) lines.add('LOCATION:$location');
  if (notes != null && notes.isNotEmpty) lines.add('DESCRIPTION:${notes.replaceAll('\n',' ')}');
  if (rrule != null && rrule.isNotEmpty) lines.add(rrule);
  lines.add('END:VEVENT');
  lines.add('END:VCALENDAR');

  final dir = await getTemporaryDirectory();
  final file = File('${dir.path}/snap2schedule_event.ics');
  await file.writeAsString(lines.join('\n'));
  return file.path;
}
