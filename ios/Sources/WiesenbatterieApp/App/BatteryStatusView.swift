import SwiftUI

struct BatteryStatusView: View {
    @EnvironmentObject private var service: MQTTBatteryService

    var body: some View {
        VStack(spacing: 24) {
            Text("Ladestand")
                .font(.title)
                .foregroundStyle(.primary)

            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(service.socValue)
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                Text("%")
                    .font(.title2)
                    .baselineOffset(8)
            }
            .foregroundColor(Color(red: 0.302, green: 0.722, blue: 1.0))

            Text("Verbindungsstatus: \(service.connectionState.statusText)")
                .font(.subheadline)
                .foregroundColor(service.connectionState.statusColor)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
        .background(Color(.systemBackground))
        .preferredColorScheme(.dark)
    }
}

#Preview {
    BatteryStatusView()
        .environmentObject(MQTTBatteryService())
}
