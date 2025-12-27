// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "WiesenbatterieApp",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .executable(
            name: "WiesenbatterieApp",
            targets: ["WiesenbatterieApp"]
        )
    ],
    dependencies: [
        .package(url: "https://github.com/emqx/CocoaMQTT.git", from: "2.1.9")
    ],
    targets: [
        .executableTarget(
            name: "WiesenbatterieApp",
            dependencies: [
                .product(name: "CocoaMQTT", package: "CocoaMQTT")
            ],
            path: "Sources"
        )
    ]
)
