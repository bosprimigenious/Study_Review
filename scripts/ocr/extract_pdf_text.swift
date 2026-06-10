import Foundation
import PDFKit
import AppKit
import Vision

if CommandLine.arguments.count < 3 {
    fputs("usage: extract_pdf_text.swift input.pdf output.txt [scale]\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
let scale = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 2.2) : 2.2

guard let document = PDFDocument(url: inputURL) else {
    fputs("cannot open PDF\n", stderr)
    exit(1)
}

func normalizedUsefulText(_ text: String?) -> String {
    guard let text else { return "" }
    let cleaned = text
        .replacingOccurrences(of: "\u{00a0}", with: " ")
        .trimmingCharacters(in: .whitespacesAndNewlines)
    return cleaned
}

struct TextQuality {
    let reliable: Bool
    let reason: String
    let replacementRatio: Double
    let readableRatio: Double
    let shortLineRatio: Double
}

func textQuality(_ text: String) -> TextQuality {
    let scalars = Array(text.unicodeScalars)
    let total = max(scalars.count, 1)
    let replacements = scalars.filter { $0.value == 0xfffd }.count
    let readable = scalars.filter { scalar in
        CharacterSet.alphanumerics.contains(scalar)
            || (scalar.value >= 0x4e00 && scalar.value <= 0x9fff)
    }.count
    let lines = text
        .split(separator: "\n", omittingEmptySubsequences: true)
        .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
    let shortSymbolLines = lines.filter { line in
        let count = line.count
        guard count > 0 && count <= 3 else { return false }
        return line.unicodeScalars.allSatisfy { scalar in
            !CharacterSet.alphanumerics.contains(scalar)
                && !(scalar.value >= 0x4e00 && scalar.value <= 0x9fff)
        }
    }.count

    let replacementRatio = Double(replacements) / Double(total)
    let readableRatio = Double(readable) / Double(total)
    let shortLineRatio = lines.isEmpty ? 0 : Double(shortSymbolLines) / Double(lines.count)

    if text.count < 20 {
        return TextQuality(reliable: false, reason: "too-short", replacementRatio: replacementRatio, readableRatio: readableRatio, shortLineRatio: shortLineRatio)
    }
    if replacements >= 8 || replacementRatio >= 0.015 {
        return TextQuality(reliable: false, reason: "replacement-character-heavy", replacementRatio: replacementRatio, readableRatio: readableRatio, shortLineRatio: shortLineRatio)
    }
    if text.count >= 120 && readableRatio < 0.25 {
        return TextQuality(reliable: false, reason: "low-readable-character-ratio", replacementRatio: replacementRatio, readableRatio: readableRatio, shortLineRatio: shortLineRatio)
    }
    if lines.count >= 20 && shortLineRatio >= 0.35 {
        return TextQuality(reliable: false, reason: "fragmented-symbol-lines", replacementRatio: replacementRatio, readableRatio: readableRatio, shortLineRatio: shortLineRatio)
    }

    return TextQuality(reliable: true, reason: "pdf-text-ok", replacementRatio: replacementRatio, readableRatio: readableRatio, shortLineRatio: shortLineRatio)
}

func pageImage(_ page: PDFPage, scale: Double) -> CGImage? {
    let bounds = page.bounds(for: .mediaBox)
    let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor.white.setFill()
    NSRect(origin: .zero, size: size).fill()
    guard let context = NSGraphicsContext.current?.cgContext else {
        image.unlockFocus()
        return nil
    }
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    context.restoreGState()
    image.unlockFocus()

    guard
        let tiff = image.tiffRepresentation,
        let bitmap = NSBitmapImageRep(data: tiff)
    else { return nil }
    return bitmap.cgImage
}

func recognize(_ cgImage: CGImage) throws -> String {
    var text = ""
    var thrown: Error?
    let semaphore = DispatchSemaphore(value: 0)

    let request = VNRecognizeTextRequest { request, error in
        defer { semaphore.signal() }
        if let error {
            thrown = error
            return
        }

        let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
        text = observations
            .compactMap { $0.topCandidates(1).first?.string }
            .joined(separator: "\n")
    }

    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try handler.perform([request])
    semaphore.wait()

    if let thrown { throw thrown }
    return text
}

var output: [String] = []
output.append("# Extracted text: \(inputURL.lastPathComponent)")
output.append("# Pages: \(document.pageCount)")
output.append("# Method: PDF text when reliable; Vision OCR fallback for image-only or garbled pages.")
output.append("")

var directPages = 0
var ocrPages = 0
var garbledFallbackPages = 0

for index in 0..<document.pageCount {
    autoreleasepool {
        output.append("===== Page \(index + 1) / \(document.pageCount) =====")
        guard let page = document.page(at: index) else {
            output.append("[page unavailable]")
            output.append("")
            return
        }

        let directText = normalizedUsefulText(page.string)
        let quality = textQuality(directText)
        if quality.reliable {
            directPages += 1
            output.append("[method: pdf-text]")
            output.append(directText)
        } else if let image = pageImage(page, scale: scale) {
            ocrPages += 1
            if directText.count >= 20 {
                garbledFallbackPages += 1
                output.append("[method: vision-ocr]")
                output.append(String(format: "[pdf-text rejected: %@, replacementRatio=%.4f, readableRatio=%.4f, shortLineRatio=%.4f]", quality.reason, quality.replacementRatio, quality.readableRatio, quality.shortLineRatio))
            } else {
                output.append("[method: vision-ocr]")
                output.append("[pdf-text rejected: \(quality.reason)]")
            }
            do {
                output.append(try recognize(image))
            } catch {
                output.append("[ocr failed: \(error)]")
            }
        } else {
            output.append("[page render failed]")
        }
        output.append("")
        print("page \(index + 1)/\(document.pageCount)")
        fflush(stdout)
    }
}

output.append("# Summary: pdf-text pages=\(directPages), ocr pages=\(ocrPages), garbled fallback pages=\(garbledFallbackPages)")

try FileManager.default.createDirectory(
    at: outputURL.deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try output.joined(separator: "\n").write(to: outputURL, atomically: true, encoding: .utf8)
print("wrote \(outputURL.path)")
