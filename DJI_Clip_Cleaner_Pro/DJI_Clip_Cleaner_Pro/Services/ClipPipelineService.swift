import Foundation

struct PipelineResult: Sendable {
    let movedToDiscard: Int
    let skippedDiscard: Int
    let keepCount: Int
    let reviewCount: Int
    let discardCount: Int
}

enum ClipPipelineService {
    private static let discardFolderName = "_DISCARD"

    static func run(
        results: [AnalysisResult],
        in folderURL: URL
    ) throws -> (pipeline: PipelineResult, keepVideos: [VideoFile]) {
        let discardFolder = folderURL.appendingPathComponent(
            discardFolderName,
            isDirectory: true
        )

        try FileManager.default.createDirectory(
            at: discardFolder,
            withIntermediateDirectories: true
        )

        var moved = 0
        var skipped = 0
        var keepVideos: [VideoFile] = []
        var reviewCount = 0
        var discardCount = 0

        for result in results {
            switch result.recommendation {
            case .discard:
                discardCount += 1
                let source = result.video.url

                guard FileManager.default.fileExists(atPath: source.path) else {
                    skipped += 1
                    continue
                }

                let destination = discardFolder.appendingPathComponent(
                    source.lastPathComponent
                )

                if FileManager.default.fileExists(atPath: destination.path) {
                    skipped += 1
                    continue
                }

                try FileManager.default.moveItem(at: source, to: destination)
                moved += 1

            case .keep:
                keepVideos.append(result.video)

            case .review:
                reviewCount += 1

            default:
                break
            }
        }

        let pipeline = PipelineResult(
            movedToDiscard: moved,
            skippedDiscard: skipped,
            keepCount: keepVideos.count,
            reviewCount: reviewCount,
            discardCount: discardCount
        )

        return (pipeline, keepVideos)
    }
}
