import SwiftUI

@main
struct WiesenbatterieApp: App {
    @StateObject private var service = MQTTBatteryService()

    var body: some Scene {
        WindowGroup {
            BatteryStatusView()
                .environmentObject(service)
        }
    }
}
