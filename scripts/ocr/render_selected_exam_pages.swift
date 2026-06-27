import Foundation
import PDFKit
import AppKit

if CommandLine.arguments.count < 3 {
    fputs("usage: render_selected_exam_pages.swift input-root output-root [scale]\n", stderr)
    exit(2)
}

let inputRoot = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputRoot = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
let scale = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 2.0) : 2.0

let selected = [
    "2015-2016 第二学期 概率论与数理统计 期末试卷【A卷】.pdf",
    "2017-2018 第一学期 概率论与数理统计 期末试卷【A卷】.pdf",
    "2018-2019 第一学期 概率论与数理统计 期末试卷【A卷】.pdf",
    "2018-2019 第二学期 概率论与数理统计 期末试卷【A卷】.pdf",
    "2019-2020 第一学期 概率论与数理统计 期末试卷【未标卷别】.pdf",
    "2019-2020 第二学期 概率论与数理统计 期末试卷【未标卷别】.pdf",
    "2020-2021 第一学期 概率论与数理统计 期末试卷【A卷-4学分】.pdf",
    "2021-2022 第二学期 概率论与数理统计 期末试卷【未标卷别-3学分】.pdf",
    "2022-2023 第一学期 概率论与数理统计试卷【A卷-4学分】.pdf",
    "2023-2024 第二学期 概率论与数理统计 期末试卷【B卷】.pdf",
    "2024-2025 第一学期 概率论与数理统计 期末试卷【A卷】.pdf",
    "2025-2026 第一学期 概率论与数理统计 期末试卷【A卷】.pdf",
]

func safeDirectoryName(_ filename: String) -> String {
    URL(fileURLWithPath: filename).deletingPathExtension().lastPathComponent
}

func render(page: PDFPage, scale: Double) -> Data? {
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
    return bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.88])
}

try FileManager.default.createDirectory(at: outputRoot, withIntermediateDirectories: true)

for filename in selected {
    let input = inputRoot.appendingPathComponent(filename)
    guard let document = PDFDocument(url: input) else {
        fputs("cannot open: \(input.path)\n", stderr)
        continue
    }
    let destination = outputRoot.appendingPathComponent(safeDirectoryName(filename), isDirectory: true)
    try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)

    for index in 0..<document.pageCount {
        autoreleasepool {
            guard let page = document.page(at: index), let data = render(page: page, scale: scale) else { return }
            let output = destination.appendingPathComponent(String(format: "page-%02d.jpg", index + 1))
            do {
                try data.write(to: output)
            } catch {
                fputs("write failed: \(output.path): \(error)\n", stderr)
            }
        }
    }
    print("rendered \(filename): \(document.pageCount) pages")
    fflush(stdout)
}
