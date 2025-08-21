
// Optional Custom Action: MLKit OCR (on-device)
// Requires dep: google_mlkit_text_recognition: ^0.13.0 (or latest)
// And camera/gallery handling via FlutterFlow or custom code.
import 'dart:io';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

Future<String> mlkitRecognizeText(String imagePath) async {
  final inputImage = InputImage.fromFile(File(imagePath));
  final textRecognizer = TextRecognizer();
  final recognizedText = await textRecognizer.processImage(inputImage);
  await textRecognizer.close();
  return recognizedText.text;
}
