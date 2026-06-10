import Foundation
import PDFKit
import AppKit

if CommandLine.arguments.count < 3 {
    fputs("usage: render_pdf_pages.swift input.pdf output-dir [scale]\n", stderr)
    exit(2)
}

let input = URL(fileURLWithPath: CommandLine.arguments[1])
let outputDir = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
let scale = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 2.0) : 2.0

try FileManager.default.createDirectory(at: outputDir, withIntermediateDirectories: true)

guard let document = PDFDocument(url: input) else {
    fputs("cannot open PDF\n", stderr)
    exit(1)
}

for index in 0..<document.pageCount {
    guard let page = document.page(at: index) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor.white.setFill()
    NSRect(origin: .zero, size: size).fill()
    guard let context = NSGraphicsContext.current?.cgContext else {
        image.unlockFocus()
        continue
    }
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    context.restoreGState()
    image.unlockFocus()

    guard
        let tiff = image.tiffRepresentation,
        let rep = NSBitmapImageRep(data: tiff),
        let png = rep.representation(using: .png, properties: [:])
    else { continue }

    let out = outputDir.appendingPathComponent(String(format: "page-%02d.png", index + 1))
    try png.write(to: out)
}

print("rendered \(document.pageCount) pages")
