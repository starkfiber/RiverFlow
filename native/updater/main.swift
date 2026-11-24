import CryptoKit
import Darwin
import Foundation

struct UpdaterError: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

let fs = FileManager.default
let executable = URL(fileURLWithPath: CommandLine.arguments[0]).resolvingSymlinksInPath()
let bundle = executable.deletingLastPathComponent()
let arguments = Array(CommandLine.arguments.dropFirst())
let maxArtifact = 1 << 20

func require(_ condition: Bool, _ message: String) throws {
    if !condition { throw UpdaterError(message) }
}

func read(_ file: URL, max limit: Int) throws -> Data {
    let fd = open(file.path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK)
    guard fd >= 0 else { throw UpdaterError("required file unavailable: \(file.lastPathComponent)") }
    let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    defer { try? handle.close() }
    var info = stat()
    try require(fstat(fd, &info) == 0 && (info.st_mode & S_IFMT) == S_IFREG,
                "expected a regular file: \(file.lastPathComponent)")
    let bytes = try handle.read(upToCount: limit + 1) ?? Data()
    try require(bytes.count <= limit, "input exceeds format size limit")
    return bytes
}

func digest(_ bytes: Data) -> Data { Data(SHA256.hash(data: bytes)) }

func hex(_ bytes: Data) -> String {
    bytes.map { String(format: "%02x", $0) }.joined()
}

func token(_ value: String) -> Bool {
    value.utf8.count == 64 && value.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
}

func sync(_ file: URL, directory: Bool = false) throws {
    let fd = open(file.path, O_RDONLY | O_NOFOLLOW | (directory ? O_DIRECTORY : 0))
    guard fd >= 0 else { throw UpdaterError("open for sync failed: \(file.lastPathComponent)") }
    defer { close(fd) }
    let result = directory ? fsync(fd) : fcntl(fd, F_FULLFSYNC)
    try require(result == 0, "sync failed: \(file.lastPathComponent)")
}

func native(_ tool: URL, _ args: [String], quiet: Bool = true) throws {
    let child = Process()
    child.executableURL = tool
    child.arguments = args
    child.standardInput = FileHandle.nullDevice
    if quiet { child.standardOutput = FileHandle.nullDevice }
    try child.run()
    child.waitUntilExit()
    try require(child.terminationReason == .exit && child.terminationStatus == 0,
                "\(tool.lastPathComponent) \(args.first ?? "") refused (status \(child.terminationStatus))")
}

func move(_ source: URL, _ destination: URL) throws {
    try require(rename(source.path, destination.path) == 0, "atomic rename failed: \(destination.lastPathComponent)")
}

func directory(_ location: URL) throws {
    try fs.createDirectory(at: location, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
}

func ownerDirectory(_ location: URL) throws {
    var info = stat()
    try require(lstat(location.path, &info) == 0 && (info.st_mode & S_IFMT) == S_IFDIR &&
                info.st_uid == geteuid() && (info.st_mode & 0o777) == 0o700,
                "trust store must be an existing owner-only (0700) directory")
}

func runExecutable(_ program: URL, _ args: [String]) throws -> Never {
    let argv = ([program.path] + args).map { strdup($0) }
    defer { argv.forEach { free($0) } }
    var terminated = argv + [nil]
    _ = terminated.withUnsafeMutableBufferPointer { execv(program.path, $0.baseAddress!) }
    throw UpdaterError("cannot launch \(program.lastPathComponent): \(String(cString: strerror(errno)))")
}

struct Store {
    let root: URL
    var authority: URL { root.appendingPathComponent("authority") }
    var generations: URL { authority.appendingPathComponent("generations") }
    var pending: URL { authority.appendingPathComponent("pending") }
    var publicKey: URL { authority.appendingPathComponent("publisher.pub") }
    var activePointer: URL { authority.appendingPathComponent("active") }

    init() throws {
        let location = try read(bundle.appendingPathComponent(".rf2-trust-location"), max: 4096)
        guard let path = String(data: location, encoding: .utf8), path.hasPrefix("/"),
              !path.contains("\n"), !path.contains("\0") else { throw UpdaterError("invalid trust store location") }
        let requested = URL(fileURLWithPath: path, isDirectory: true)
        root = requested.standardizedFileURL.resolvingSymlinksInPath()
        try require(root.path == requested.path, "trust store location must be canonical")
        try require(root.path != bundle.path && !root.path.hasPrefix(bundle.path + "/"),
                    "trust store must be outside the installed bundle")
        try ownerDirectory(root)
    }

    func locked<T>(_ operation: () throws -> T) throws -> T {
        let fd = open(root.appendingPathComponent("writer.lock").path, O_CREAT | O_RDWR | O_NOFOLLOW | O_CLOEXEC, 0o600)
        guard fd >= 0 else { throw UpdaterError("cannot open updater lock") }
        defer { close(fd) }
        try require(flock(fd, LOCK_EX) == 0, "cannot lock updater")
        return try operation()
    }

    func checkedKey() throws -> Data {
        try ownerDirectory(authority)
        let raw = try read(publicKey, max: 65)
        let pin = try read(authority.appendingPathComponent("publisher.sha256"), max: 64)
        try require(raw.count == 65 && raw.first == 4 && Data(hex(digest(raw)).utf8) == pin,
                    "publisher key differs from enrolled key")
        return raw
    }

    func snapshot() throws -> URL {
        let key = try checkedKey()
        let id = try read(activePointer, max: 64)
        guard let name = String(data: id, encoding: .ascii), token(name) else {
            throw UpdaterError("malformed active generation")
        }
        let slot = generations.appendingPathComponent(name)
        let record = try read(slot.appendingPathComponent("record"), max: 376)
        let signedRecord = try ReleaseRecord(record, publisher: key)
        let checkpoint = try read(slot.appendingPathComponent("checkpoint"), max: 80)
        try require(record.count >= 304 && checkpoint.count == 80 &&
                    checkpoint.prefix(8) == Data("RF2PIN01".utf8) &&
                    checkpoint[8..<40] == digest(key) && checkpoint[48..<80] == digest(record) &&
                    checkpoint[40..<48] == record[16..<24] && hex(digest(record)) == name,
                    "active checkpoint and signed release record disagree")
        let image = try read(slot.appendingPathComponent("rf2c"), max: maxArtifact)
        try require(digest(image) == signedRecord.artifact, "active compiler differs from signed artifact")
        return slot
    }

    func history(_ slot: URL) throws -> ReleaseHistory {
        try ReleaseHistory(publisher: checkedKey(), state: read(slot.appendingPathComponent("state"), max: stateLimit),
                           checkpoint: read(slot.appendingPathComponent("checkpoint"), max: 80))
    }

    func materialize(_ input: URL, _ slot: URL, history: ReleaseHistory) throws {
        var history = history
        let record = try read(input.appendingPathComponent("record"), max: recordLimit)
        let image = try read(input.appendingPathComponent("artifact"), max: maxArtifact)
        try history.accept(record, artifact: image)
        try history.state.write(to: slot.appendingPathComponent("state"))
        try history.checkpoint.write(to: slot.appendingPathComponent("checkpoint"))
        let compiler = slot.appendingPathComponent("rf2c")
        try image.write(to: compiler)
        try require(chmod(compiler.path, 0o700) == 0, "cannot mark compiler executable")
        try native(URL(fileURLWithPath: "/usr/bin/codesign"), ["--verify", "--strict", compiler.path])
        try record.write(to: slot.appendingPathComponent("record"))
        for name in ["state", "checkpoint", "rf2c", "record"] { try sync(slot.appendingPathComponent(name)) }
        try sync(slot, directory: true)
    }

    func inputs(_ target: URL, record: String, artifact: String) throws -> String {
        let bytes = try read(URL(fileURLWithPath: record), max: 376)
        let image = try read(URL(fileURLWithPath: artifact), max: maxArtifact)
        try bytes.write(to: target.appendingPathComponent("record"))
        try image.write(to: target.appendingPathComponent("artifact"))
        try sync(target.appendingPathComponent("record"))
        try sync(target.appendingPathComponent("artifact"))
        try sync(target, directory: true)
        return hex(digest(bytes))
    }

    func enroll(_ sourceKey: String, _ pin: String, _ record: String, _ image: String) throws {
        try locked {
            // An existing authority, including a damaged one, is never reset by enrollment.
            var info = stat()
            try require(lstat(authority.path, &info) < 0 && errno == ENOENT, "trust store already enrolled")
            let raw = try read(URL(fileURLWithPath: sourceKey), max: 65)
            try require(token(pin) && raw.count == 65 && raw.first == 4 && hex(digest(raw)) == pin,
                        "publisher key does not match independently provided SHA-256")
            let draft = root.appendingPathComponent(".enroll-" + UUID().uuidString)
            try directory(draft)
            defer { try? fs.removeItem(at: draft) }
            let key = draft.appendingPathComponent("publisher.pub")
            try raw.write(to: key)
            try Data(pin.utf8).write(to: draft.appendingPathComponent("publisher.sha256"))
            let generations = draft.appendingPathComponent("generations")
            try directory(generations)
            try directory(draft.appendingPathComponent("pending"))
            let input = draft.appendingPathComponent("input")
            try directory(input)
            let id = try inputs(input, record: record, artifact: image)
            let slot = generations.appendingPathComponent(id)
            try directory(slot)
            try materialize(input, slot, history: ReleaseHistory(publisher: raw))
            try fs.removeItem(at: input)
            for name in ["publisher.pub", "publisher.sha256"] { try sync(draft.appendingPathComponent(name)) }
            let pointer = draft.appendingPathComponent("active")
            try Data(id.utf8).write(to: pointer)
            try sync(pointer)
            try sync(generations, directory: true)
            try sync(draft, directory: true)
            try move(draft, authority)
            try sync(root, directory: true)
        }
    }

    func prepare(_ record: String, _ artifact: String) throws -> String {
        try locked {
            let current = try snapshot()
            let staging = pending.appendingPathComponent(".prepare-" + UUID().uuidString)
            try directory(staging)
            defer { try? fs.removeItem(at: staging) }
            let id = try inputs(staging, record: record, artifact: artifact)
            let validated = staging.appendingPathComponent("validated")
            try directory(validated)
            try materialize(staging, validated, history: history(current))
            try fs.removeItem(at: validated)
            let destination = pending.appendingPathComponent(id)
            // A repeated prepare of the same unapplied record refreshes its verified payload.
            if fs.fileExists(atPath: destination.path) { try fs.removeItem(at: destination) }
            try move(staging, destination)
            try sync(pending, directory: true)
            return id
        }
    }

    func activate(_ id: String) throws {
        try require(token(id), "invalid prepared update ID")
        try locked {
            let current = try snapshot()
            let input = pending.appendingPathComponent(id)
            try require(try hex(digest(read(input.appendingPathComponent("record"), max: 376))) == id,
                        "prepared record differs from requested update ID")
            let slot = generations.appendingPathComponent(id)
            try require(slot != current, "release already active")
            let draft = generations.appendingPathComponent(".activate-" + UUID().uuidString)
            try directory(draft)
            defer { try? fs.removeItem(at: draft) }
            try materialize(input, draft, history: history(current))
            if fs.fileExists(atPath: slot.path) {
                // A prior process may have published the complete generation before switching.
                for (name, limit) in [("state", 16 << 20), ("checkpoint", 80), ("record", 376), ("rf2c", maxArtifact)] {
                    let expected = try read(draft.appendingPathComponent(name), max: limit)
                    let retained = try read(slot.appendingPathComponent(name), max: limit)
                    try require(expected == retained, "retained generation differs from verified update")
                }
            } else {
                try move(draft, slot)
            }
            try sync(generations, directory: true)
            let pointer = authority.appendingPathComponent(".active-" + UUID().uuidString)
            defer { try? fs.removeItem(at: pointer) }
            try Data(id.utf8).write(to: pointer)
            try sync(pointer)
            try move(pointer, activePointer)
            try sync(authority, directory: true)
        }
    }
}

do {
    if executable.lastPathComponent == "rf2c" {
        let slot = try Store().snapshot()
        try runExecutable(slot.appendingPathComponent("rf2c"), arguments)
    }
    guard arguments.first == "update" else {
        try runExecutable(bundle.appendingPathComponent("libexec/rf2-core"), arguments)
    }
    let action = Array(arguments.dropFirst())
    if action == ["--help"] || action.isEmpty {
        print("""
        rf2 update enroll PUBLIC_KEY INDEPENDENT_SHA256 GENESIS_RECORD ARTIFACT
        rf2 update prepare RECORD ARTIFACT
        rf2 update activate PREPARED_ID
        rf2 update status
        Rollback uses prepare and activate with a signed rollback record.
        """)
        exit(0)
    }
    let store = try Store()
    switch action.first {
    case "enroll" where action.count == 5:
        try store.enroll(action[1], action[2], action[3], action[4])
        print("enrolled")
    case "prepare" where action.count == 3:
        print(try store.prepare(action[1], action[2]))
    case "activate" where action.count == 2:
        try store.activate(action[1])
        print("activated")
    case "status" where action.count == 1:
        let slot = try store.snapshot()
        let verified = try store.history(slot)
        try require(hex(verified.head) == slot.lastPathComponent, "history head differs from active release")
        print(slot.lastPathComponent)
    default:
        throw UpdaterError("invalid update arguments; see rf2 update --help")
    }
} catch {
    FileHandle.standardError.write(Data("rf2: \(error)\n".utf8))
    exit(2)
}
