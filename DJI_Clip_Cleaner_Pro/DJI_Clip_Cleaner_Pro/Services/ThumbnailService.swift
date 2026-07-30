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
        outputURL: URL,
        at timeSeconds: TimeInterval? = nil
    ) async throws {
        let frame = try await captureFrame(from: videoURL, at: timeSeconds)
        try await generate(from: frame, title: title, brand: brand, outputURL: outputURL)
    }

    static func generate(
        from frame: CGImage,
        title: String,
        brand: BrandSettingsValues,
        outputURL: URL
    ) async throws {
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

    private static func captureFrame(
        from videoURL: URL,
        at timeSeconds: TimeInterval? = nil
    ) async throws -> CGImage {
        let asset = AVURLAsset(url: videoURL)
        let duration = try await asset.load(.duration)
        let seconds = CMTimeGetSeconds(duration)
        let sampleTime = timeSeconds ?? max(seconds * 0.25, 0.5)
        let time = CMTime(
            seconds: min(max(sampleTime, 0), max(seconds - 0.1, 0)),
            preferredTimescale: 600
        )

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

        let displayTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        let emojis = Array(brand.thumbnailEmojis.prefix(ThumbnailEmojiOption.maximumSelection))

        guard !displayTitle.isEmpty || !emojis.isEmpty else {
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

        let inset: CGFloat = 48
        var availableWidth = canvasSize.width - (inset * 2)
        var textSuffix = ""

        // Beside-title placement appends the emoji so it sits with the letters.
        if brand.emojiPosition == .besideTitle, !emojis.isEmpty {
            textSuffix = " " + emojis.joined(separator: " ")
        }

        let composedTitle = displayTitle.isEmpty
            ? textSuffix.trimmingCharacters(in: .whitespaces)
            : displayTitle + textSuffix

        let paragraph = NSMutableParagraphStyle()
        paragraph.alignment = .left
        paragraph.lineBreakMode = .byWordWrapping

        if !composedTitle.isEmpty {
            let scale = CGFloat(min(max(brand.titleScale, 0.6), 1.6))

            // Corner emojis need a little less width so long titles do not run
            // underneath them when both are large.
            if brand.emojiPosition != .besideTitle, !emojis.isEmpty {
                availableWidth -= canvasSize.width * 0.12
            }

            let (font, textSize) = fittedFont(
                for: composedTitle,
                maxWidth: availableWidth,
                maxHeight: canvasSize.height * min(0.42 * scale, 0.70),
                canvasWidth: canvasSize.width,
                scale: scale,
                paragraph: paragraph
            )

            // Size the scrim to the text so short text gets a tight band and long
            // text still stays readable instead of overflowing a fixed bar.
            let barHeight = min(textSize.height + (inset * 1.6), canvasSize.height * 0.82)
            let barRect = CGRect(
                x: 0,
                y: 0,
                width: canvasSize.width,
                height: barHeight
            )

            let gradientColors = [
                NSColor.black.withAlphaComponent(0.0).cgColor,
                NSColor.black.withAlphaComponent(0.88).cgColor
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

            let textRect = CGRect(
                x: inset,
                y: (barHeight - textSize.height) / 2,
                width: availableWidth,
                height: textSize.height
            )

            drawOutlinedTitle(
                composedTitle,
                in: textRect,
                font: font,
                fillColor: titleColor,
                paragraph: paragraph
            )

            // Beside-title emojis are already drawn as part of composedTitle.
            if brand.emojiPosition != .besideTitle {
                drawCornerEmojis(
                    emojis,
                    position: brand.emojiPosition,
                    canvasSize: canvasSize,
                    scale: scale
                )
            }
        } else {
            drawCornerEmojis(
                emojis,
                position: brand.emojiPosition == .besideTitle ? .topRight : brand.emojiPosition,
                canvasSize: canvasSize,
                scale: CGFloat(min(max(brand.titleScale, 0.6), 1.6))
            )
        }

        return image
    }

    private static func drawCornerEmojis(
        _ emojis: [String],
        position: ThumbnailEmojiPosition,
        canvasSize: NSSize,
        scale: CGFloat
    ) {
        guard !emojis.isEmpty else { return }

        let size = canvasSize.width * 0.11 * scale
        let padding = canvasSize.width * 0.035
        // AppKit text origin is bottom-left; y grows upward.
        let topY = canvasSize.height - padding - size

        let font = NSFont.systemFont(ofSize: size)
        let attributes: [NSAttributedString.Key: Any] = [.font: font]

        func draw(_ emoji: String, at point: CGPoint) {
            (emoji as NSString).draw(at: point, withAttributes: attributes)
        }

        switch position {
        case .topRight:
            for (index, emoji) in emojis.enumerated() {
                let x = canvasSize.width - padding - size - (CGFloat(index) * (size * 0.85))
                draw(emoji, at: CGPoint(x: x, y: topY))
            }

        case .topLeft:
            for (index, emoji) in emojis.enumerated() {
                let x = padding + (CGFloat(index) * (size * 0.85))
                draw(emoji, at: CGPoint(x: x, y: topY))
            }

        case .bothTop:
            if let first = emojis.first {
                draw(first, at: CGPoint(x: padding, y: topY))
            }

            if emojis.count > 1 {
                draw(
                    emojis[1],
                    at: CGPoint(x: canvasSize.width - padding - size, y: topY)
                )
            } else if let first = emojis.first {
                // One emoji still lands top-right when "both" is selected.
                draw(
                    first,
                    at: CGPoint(x: canvasSize.width - padding - size, y: topY)
                )
            }

        case .besideTitle:
            break
        }
    }

    /// Starts large and steps down only until the text fits. Short thumbnail
    /// text ends up big enough to read on a phone-sized preview.
    private static func fittedFont(
        for text: String,
        maxWidth: CGFloat,
        maxHeight: CGFloat,
        canvasWidth: CGFloat,
        scale: CGFloat,
        paragraph: NSParagraphStyle
    ) -> (NSFont, CGSize) {
        let largestSize = canvasWidth * 0.135 * scale
        let smallestSize = canvasWidth * 0.038 * scale
        var size = largestSize
        var font = NSFont.boldSystemFont(ofSize: size)
        var measured = measure(text, font: font, maxWidth: maxWidth, paragraph: paragraph)

        // Word wrapping cannot break inside a single long word, so width has to
        // be checked too or that word renders past the canvas edge.
        while size > smallestSize && (measured.height > maxHeight || measured.width > maxWidth) {
            size -= canvasWidth * 0.004
            font = NSFont.boldSystemFont(ofSize: size)
            measured = measure(text, font: font, maxWidth: maxWidth, paragraph: paragraph)
        }

        return (font, measured)
    }

    private static func measure(
        _ text: String,
        font: NSFont,
        maxWidth: CGFloat,
        paragraph: NSParagraphStyle
    ) -> CGSize {
        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .paragraphStyle: paragraph
        ]

        let bounds = (text as NSString).boundingRect(
            with: CGSize(width: maxWidth, height: .greatestFiniteMagnitude),
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: attributes
        )

        return CGSize(width: bounds.width, height: ceil(bounds.height))
    }

    private static func drawOutlinedTitle(
        _ title: String,
        in rect: CGRect,
        font: NSFont,
        fillColor: NSColor,
        paragraph: NSParagraphStyle
    ) {
        let drawOptions: NSString.DrawingOptions = [
            .usesLineFragmentOrigin,
            .usesFontLeading
        ]

        let whiteOutlineWidth = max(font.pointSize * 0.24, 7.0)
        let blackOutlineWidth = max(font.pointSize * 0.14, 4.0)

        let whiteOutlineAttributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: NSColor.clear,
            .strokeColor: NSColor.white,
            .strokeWidth: whiteOutlineWidth,
            .paragraphStyle: paragraph
        ]

        let blackOutlineAttributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: NSColor.clear,
            .strokeColor: NSColor.black,
            .strokeWidth: blackOutlineWidth,
            .paragraphStyle: paragraph
        ]

        let fillAttributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: fillColor,
            .paragraphStyle: paragraph
        ]

        title.draw(with: rect, options: drawOptions, attributes: whiteOutlineAttributes)
        title.draw(with: rect, options: drawOptions, attributes: blackOutlineAttributes)
        title.draw(with: rect, options: drawOptions, attributes: fillAttributes)
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

    #endif
}
