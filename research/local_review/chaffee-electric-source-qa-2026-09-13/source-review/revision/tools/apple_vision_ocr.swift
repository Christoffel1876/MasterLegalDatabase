// On-device OCR for one complete page image. No network or source PDF writes.
import Foundation
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("Expected one page-image path".utf8))
    exit(2)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en-US"]
request.usesLanguageCorrection = false
request.automaticallyDetectsLanguage = false
request.minimumTextHeight = 0
request.revision = VNRecognizeTextRequestRevision3
request.usesCPUOnly = true
let handler = VNImageRequestHandler(
    url: URL(fileURLWithPath: CommandLine.arguments[1]), options: [:])
do {
    try handler.perform([request])
    let lines: [[String: Any]] = (request.results ?? []).map { observation in
        guard let candidate = observation.topCandidates(1).first else {
            return ["text": "", "confidence": 0.0,
                    "bbox": [0.0, 0.0, 0.0, 0.0]]
        }
        let box = observation.boundingBox
        return ["text": candidate.string, "confidence": Double(candidate.confidence),
                "bbox": [Double(box.origin.x), Double(box.origin.y),
                         Double(box.width), Double(box.height)]]
    }
    let object: [String: Any] = ["revision": request.revision,
        "os_version": ProcessInfo.processInfo.operatingSystemVersionString, "lines": lines]
    let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
} catch {
    FileHandle.standardError.write(Data(String(describing: error).utf8))
    exit(1)
}
