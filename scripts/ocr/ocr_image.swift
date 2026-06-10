import Foundation
import AppKit
import Vision

if CommandLine.arguments.count < 2 {
    fputs("usage: ocr_image.swift image.png [languages comma-separated]\n", stderr)
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
let languages = CommandLine.arguments.count >= 3
    ? CommandLine.arguments[2].split(separator: ",").map(String.init)
    : ["zh-Hans", "en-US"]

guard
    let image = NSImage(contentsOf: imageURL),
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let cgImage = bitmap.cgImage
else {
    fputs("cannot open image\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest { request, error in
    if let error {
        fputs("ocr error: \(error)\n", stderr)
        exit(1)
    }

    let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
    let lines = observations.compactMap { observation in
        observation.topCandidates(1).first?.string
    }
    print(lines.joined(separator: "\n"))
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = languages

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])
