import SwiftUI

struct ManualView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                hero
                workflowSection
                settingsSection
                tabsSection
                requirementsSection
                changelogSection
                footer
            }
            .padding(28)
        }
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                Image(systemName: "book.closed.fill")
                    .font(.system(size: 34))
                    .foregroundStyle(AppTheme.papaya)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Workflow Guide")
                        .font(.largeTitle.bold())
                        .foregroundStyle(AppTheme.carbon)

                    Text("\(AppIdentity.name) v\(AppManual.lastUpdatedVersion)")
                        .font(.headline)
                        .foregroundStyle(AppTheme.mclarenBlue)
                }

                Spacer()

                Text("Updated v\(AppManual.lastUpdatedVersion)")
                    .font(.caption.bold())
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(AppTheme.softOrange)
                    .foregroundStyle(AppTheme.papaya)
                    .clipShape(Capsule())
            }

            Text(AppIdentity.tagline)
                .foregroundStyle(.secondary)

            Text(
                "Use this guide before every shoot folder. Hughes Clip Prep sorts junk, trims dead air, polishes audio, and can smooth shaky camera movement so Filmora gets cleaner source material."
            )
            .foregroundStyle(.secondary)
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(AppTheme.softBlue)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(AppTheme.heroGradient, lineWidth: 2)
        )
    }

    private var workflowSection: some View {
        manualGroup(
            title: "How To Prepare A Shoot Folder",
            icon: "list.number"
        ) {
            VStack(alignment: .leading, spacing: 14) {
                ForEach(
                    Array(AppManual.workflowSteps.enumerated()),
                    id: \.offset
                ) { index, step in
                    HStack(alignment: .top, spacing: 12) {
                        Text("\(index + 1)")
                            .font(.caption.bold())
                            .frame(width: 24, height: 24)
                            .background(AppTheme.papaya)
                            .foregroundStyle(.white)
                            .clipShape(Circle())

                        Text(step)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
        }
    }

    private var settingsSection: some View {
        manualGroup(
            title: "Recommended Settings",
            icon: "slider.horizontal.3"
        ) {
            VStack(alignment: .leading, spacing: 16) {
                ForEach(AppManual.recommendedSettings) { section in
                    manualCard(section)
                }
            }
        }
    }

    private var tabsSection: some View {
        manualGroup(
            title: "What Each Tab Does",
            icon: "square.grid.2x2"
        ) {
            VStack(alignment: .leading, spacing: 16) {
                ForEach(AppManual.tabGuide) { section in
                    manualCard(section)
                }
            }
        }
    }

    private var requirementsSection: some View {
        manualGroup(
            title: "Required Tools",
            icon: "shippingbox.fill"
        ) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(AppManual.requirements, id: \.self) { item in
                    Label(item, systemImage: "checkmark.circle.fill")
                        .foregroundStyle(AppTheme.mclarenBlue)
                }
            }
        }
    }

    private var changelogSection: some View {
        manualGroup(
            title: "What Changed",
            icon: "clock.arrow.circlepath"
        ) {
            VStack(alignment: .leading, spacing: 18) {
                ForEach(AppManual.changelog) { entry in
                    VStack(alignment: .leading, spacing: 8) {
                        Text("v\(entry.version)")
                            .font(.headline)
                            .foregroundStyle(AppTheme.papaya)

                        ForEach(entry.highlights, id: \.self) { highlight in
                            HStack(alignment: .top, spacing: 8) {
                                Text("•")
                                    .foregroundStyle(AppTheme.mclarenBlue)
                                Text(highlight)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }

                    if entry.version != AppManual.changelog.last?.version {
                        Divider()
                    }
                }
            }
        }
    }

    private var footer: some View {
        Text(
            "To update \(AppIdentity.name), double-click Update.command inside Desktop/\(AppIdentity.desktopFolderName)/. Look for the version badge in Smart Analysis to confirm you are on the latest build."
        )
        .font(.caption)
        .foregroundStyle(.secondary)
    }

    @ViewBuilder
    private func manualGroup<Content: View>(
        title: String,
        icon: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        GroupBox {
            content()
                .padding(4)
        } label: {
            Label(title, systemImage: icon)
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private func manualCard(_ section: ManualSection) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: section.icon)
                .foregroundStyle(AppTheme.papaya)
                .frame(width: 22)

            VStack(alignment: .leading, spacing: 4) {
                Text(section.title)
                    .fontWeight(.semibold)
                Text(section.body)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AppTheme.softOrange)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

#Preview {
    ManualView()
}
