import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            CleanerView()
                .tabItem {
                    Label("Clip Cleaner", systemImage: "sparkles")
                }

            AnalysisView()
                .tabItem {
                    Label("Smart Analysis", systemImage: "waveform.badge.magnifyingglass")
                }
        }
    }
}

#Preview {
    MainTabView()
}
