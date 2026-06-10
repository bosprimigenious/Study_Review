import Foundation
import PDFKit
import AppKit
import Vision

if CommandLine.arguments.count < 3 {
    fputs("usage: extract_probability_pdfs.swift input-root output-root [scale]\n", stderr)
    exit(2)
}

let inputRoot = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputRoot = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
let scale = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 2.0) : 2.0

func pdfFiles(under root: URL) -> [URL] {
    let keys: [URLResourceKey] = [.isRegularFileKey]
    guard let enumerator = FileManager.default.enumerator(
        at: root,
        includingPropertiesForKeys: keys,
        options: [.skipsHiddenFiles]
    ) else { return [] }

    return enumerator.compactMap { item -> URL? in
        guard let url = item as? URL, url.pathExtension.lowercased() == "pdf" else { return nil }
        return url
    }.sorted { $0.path < $1.path }
}

func outputURL(for input: URL) -> URL {
    let rootPath = inputRoot.standardizedFileURL.path
    var relative = input.standardizedFileURL.path
    if relative.hasPrefix(rootPath) {
        relative.removeFirst(rootPath.count)
    }
    relative = relative.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    let withoutExt = (relative as NSString).deletingPathExtension
    return outputRoot.appendingPathComponent(withoutExt + ".txt")
}

func normalizedUsefulText(_ text: String?) -> String {
    guard let text else { return "" }
    return text
        .replacingOccurrences(of: "\u{00a0}", with: " ")
        .trimmingCharacters(in: .whitespacesAndNewlines)
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

func extract(_ input: URL, to output: URL) {
    guard let document = PDFDocument(url: input) else {
        fputs("cannot open PDF: \(input.path)\n", stderr)
        return
    }

    var lines: [String] = []
    lines.append("# Extracted text: \(input.lastPathComponent)")
    lines.append("# Source: \(input.path)")
    lines.append("# Pages: \(document.pageCount)")
    lines.append("# Method: PDF text when reliable; Vision OCR fallback for image-only or garbled pages.")
    lines.append("")

    var directPages = 0
    var ocrPages = 0
    var garbledFallbackPages = 0

    for index in 0..<document.pageCount {
        autoreleasepool {
            lines.append("===== Page \(index + 1) / \(document.pageCount) =====")
            guard let page = document.page(at: index) else {
                lines.append("[page unavailable]")
                lines.append("")
                return
            }

            let directText = normalizedUsefulText(page.string)
            let quality = textQuality(directText)
            if quality.reliable {
                directPages += 1
                lines.append("[method: pdf-text]")
                lines.append(directText)
            } else if let image = pageImage(page, scale: scale) {
                ocrPages += 1
                lines.append("[method: vision-ocr]")
                if directText.count >= 20 {
                    garbledFallbackPages += 1
                    lines.append(String(format: "[pdf-text rejected: %@, replacementRatio=%.4f, readableRatio=%.4f, shortLineRatio=%.4f]", quality.reason, quality.replacementRatio, quality.readableRatio, quality.shortLineRatio))
                } else {
                    lines.append("[pdf-text rejected: \(quality.reason)]")
                }
                do {
                    lines.append(try recognize(image))
                } catch {
                    lines.append("[ocr failed: \(error)]")
                }
            } else {
                lines.append("[page render failed]")
            }
            lines.append("")
        }
    }

    lines.append("# Summary: pdf-text pages=\(directPages), ocr pages=\(ocrPages), garbled fallback pages=\(garbledFallbackPages)")

    do {
        try FileManager.default.createDirectory(
            at: output.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try lines.joined(separator: "\n").write(to: output, atomically: true, encoding: .utf8)
        print("wrote \(output.path) [pages=\(document.pageCount), pdf-text=\(directPages), ocr=\(ocrPages), garbled-fallback=\(garbledFallbackPages)]")
    } catch {
        fputs("write failed: \(output.path): \(error)\n", stderr)
    }
}

let files = pdfFiles(under: inputRoot)
print("found \(files.count) pdf files")

for (index, input) in files.enumerated() {
    print("[\(index + 1)/\(files.count)] \(input.path)")
    extract(input, to: outputURL(for: input))
    fflush(stdout)
}
