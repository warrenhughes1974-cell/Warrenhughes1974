import AVFoundation
import Foundation

#if canImport(AppKit)
import AppKit
#endif

enum ThumbnailService {
    enum ServiceError: LocalizedError {
        case frameCaptureFailed
        case renderFailed
        case writeFailed

        var errorDescription: String? {
            switch self {
            case .frameCaptureFailed:
                return "Could not capture a frame for the thumbnail."
            case .renderFailed:
                return "Could not render the branded thumbnail."
            case .writeFailed:
                return "Could not save the thumbnail image."
            }
        }
    }

    static let outputFolderName = "Thumbnails"
    static let thumbnailWidth = 1280
    static let thumbnailHeight = 720

    static func generate(
        from videoURL: URL,
        title: String,
        brand: BrandSettingsValues,
        outputURL: URL
    ) async throws {
        let frame = try await captureFrame(from: videoURL)

        #if canImport(AppKit)
        guard let image = renderBrandedThumbnail(
            frame: frame,
            title: title,
            brand: brand
        ) else {
            throw ServiceError.renderFailed
        }

        guard let tiffData = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData),
              let jpegData = bitmap.representation(
                using: .jpeg,
                properties: [.compressionFactor: 0.9]
              ) else {
            throw ServiceError.writeFailed
        }

        try jpegData.write(to: outputURL, options: .atomic)
        #else
        throw ServiceError.renderFailed
        #endif
    }

    private static func captureFrame(from videoURL: URL) async throws -> CGImage {
        let asset = AVURLAsset(url: videoURL)
        let duration = try await asset.load(.duration)
        let seconds = CMTimeGetSeconds(duration)
        let sampleTime = max(seconds * 0.25, 0.5)
        let time = CMTime(seconds: min(sampleTime, max(seconds - 0.1, 0)), preferredTimescale: 600)

        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 1920, height: 1080)
        generator.requestedTimeToleranceBefore = CMTime(seconds: 0.5, preferredTimescale: 600)
        generator.requestedTimeToleranceAfter = CMTime(seconds: 0.5, preferredTimescale: 600)

        return try await withCheckedThrowingContinuation { continuation in
            generator.generateCGImageAsynchronously(for: time) { image, _, error in
                if let image {
                    continuation.resume(returning: image)
                } else {
                    continuation.resume(throwing: error ?? ServiceError.frameCaptureFailed)
                }
            }
        }
    }

    #if canImport(AppKit)
    private static func renderBrandedThumbnail(
        frame: CGImage,
        title: String,
        brand: BrandSettingsValues
    ) -> NSImage? {
        let canvasSize = NSSize(
            width: CGFloat(thumbnailWidth),
            height: CGFloat(thumbnailHeight)
        )

        let image = NSImage(size: canvasSize)
        image.lockFocus()

        defer {
            image.unlockFocus()
        }

        guard let context = NSGraphicsContext.current?.cgContext else {
            return nil
        }

        let frameRect = aspectFillRect(
            imageSize: CGSize(width: frame.width, height: frame.height),
            in: CGRect(origin: .zero, size: canvasSize)
        )

        context.saveGState()
        context.addRect(CGRect(origin: .zero, size: canvasSize))
        context.clip()
        context.draw(frame, in: frameRect)
        context.restoreGState()

        let barHeight = canvasSize.height * 0.24
        let barRect = CGRect(
            x: 0,
            y: 0,
            width: canvasSize.width,
            height: barHeight
        )

        let gradientColors = [
            NSColor.black.withAlphaComponent(0.0).cgColor,
            NSColor.black.withAlphaComponent(0.82).cgColor
        ] as CFArray

        if let gradient = CGGradient(
            colorsSpace: CGColorSpaceCreateDeviceRGB(),
            colors: gradientColors,
            locations: [0.0, 1.0]
        ) {
            context.saveGState()
            context.clip(to: barRect)
            context.drawLinearGradient(
                gradient,
                start: CGPoint(x: barRect.midX, y: barRect.maxY),
                end: CGPoint(x: barRect.midX, y: barRect.minY),
                options: []
            )
            context.restoreGState()
        }

        let displayTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !displayTitle.isEmpty else {
            return image
        }

        let titleColor: NSColor
        if brand.usePinkTitles {
            titleColor = NSColor(
                calibratedRed: brand.titlePinkRed,
                green: brand.titlePinkGreen,
                blue: brand.titlePinkBlue,
                alpha: 1.0
            )
        } else {
            titleColor = .white
        }

        let fontSize = fontSizeForTitle(displayTitle, canvasWidth: canvasSize.width)
        let font = NSFont.boldSystemFont(ofSize: fontSize)

        let paragraph = NSMutableParagraphStyle()
        paragraph.alignment = .left
        paragraph.lineBreakMode = .byWordWrapping

        let inset: CGFloat = 36
        let textRect = CGRect(
            x: inset,
            y: inset * 0.55,
            width: canvasSize.width - (inset * 2),
            height: barHeight - inset
        )

        drawOutlinedTitle(
            displayTitle,
            in: textRect,
            font: font,
            fillColor: titleColor,
            paragraph: paragraph
        )

        return image
    }

    private static func drawOutlinedTitle(
        _ title: String,
        in rect: CGRect,
        font: NSFont,
        fillColor: NSColor,
        paragraph: NSParagraphStyle
    ) {
        let outlineWidth = max(font.pointSize * 0.14, 4.0)

        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: fillColor,
            .strokeColor: NSColor.black,
            .strokeWidth: -outlineWidth,
            .paragraphStyle: paragraph
        ]

        title.draw(
            with: rect,
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: attributes
        )
    }

    private static func aspectFillRect(
        imageSize: CGSize,
        in bounds: CGRect
    ) -> CGRect {
        guard imageSize.width > 0, imageSize.height > 0 else {
            return bounds
        }

        let widthScale = bounds.width / imageSize.width
        let heightScale = bounds.height / imageSize.height
        let scale = max(widthScale, heightScale)

        let scaledSize = CGSize(
            width: imageSize.width * scale,
            height: imageSize.height * scale
        )

        return CGRect(
            x: bounds.midX - scaledSize.width / 2,
            y: bounds.midY - scaledSize.height / 2,
            width: scaledSize.width,
            height: scaledSize.height
        )
    }

    private static func fontSizeForTitle(_ title: String, canvasWidth: CGFloat) -> CGFloat {
        let length = title.count

        if length > 70 {
            return canvasWidth * 0.038
        }

        if length > 45 {
            return canvasWidth * 0.045
        }

        return canvasWidth * 0.052
    }
    #endif
}
