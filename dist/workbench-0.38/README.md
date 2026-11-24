# RF2 Workbench 0.38 development edition

[Download the Apple Silicon Mac bundle](RF2-Workbench-0.38-dev-macos-arm64.zip) · [SHA-256](RF2-Workbench-0.38-dev-macos-arm64.zip.sha256) · [Walkthrough and limits](../../docs/BOOKING-STUDIO.md)

Booking CLI, graphical booking and Core learning IDE, with the unchanged native compiler and nine-tool MCP runtime. No Node/npm/Python user runtime. macOS ad-hoc signing remains subject to normal OS security checks; this is not a notarized installer.

SHA-256: `146874d9b68b2c4a4be373f967e7ea04b7490da4abc69e8df1717be3acb0c8c7`

Extract the archive, open Terminal in the extracted folder and follow README.md. `booking init` creates a new journal. `booking-web` prints its local URL. `studio` requires an explicitly selected private project directory and absolute bundle paths. The IDE supports bounded Core programs; it is not a full systems IDE.

An optional [managed-update build](../../native/updater/README.md) uses this pinned bundle and separately provisioned publisher trust. The base download remains available.
