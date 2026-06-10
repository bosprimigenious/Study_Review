import Foundation
import PDFKit
import AppKit
import Vision

if CommandLine.arguments.count < 3 {
    fputs("usage: ocr_pdf.swift input.pdf output.txt [scale]\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
let scale = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 2.5) : 2.5

guard let document = PDFDocument(url: inputURL) else {
    fputs("cannot open PDF\n", stderr)
    exit(1)
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
output.append("# OCR: \(inputURL.lastPathComponent)")
output.append("# Pages: \(document.pageCount)")
output.append("")

for index in 0..<document.pageCount {
    autoreleasepool {
        output.append("===== Page \(index + 1) / \(document.pageCount) =====")
        guard let page = document.page(at: index), let image = pageImage(page, scale: scale) else {
            output.append("[page render failed]")
            output.append("")
            return
        }

        do {
            output.append(try recognize(image))
        } catch {
            output.append("[ocr failed: \(error)]")
        }
        output.append("")
        print("ocr \(index + 1)/\(document.pageCount)")
        fflush(stdout)
    }
}

try FileManager.default.createDirectory(
    at: outputURL.deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try output.joined(separator: "\n").write(to: outputURL, atomically: true, encoding: .utf8)
print("wrote \(outputURL.path)")
