import CryptoKit
import Foundation

let stateLimit = 16 << 20
let recordLimit = 376

private func word(_ value: UInt64) -> Data {
    var little = value.littleEndian
    return withUnsafeBytes(of: &little) { Data($0) }
}

private func word(_ raw: Data, _ offset: Int) -> UInt64 {
    raw.subdata(in: offset..<offset + 8).withUnsafeBytes {
        UInt64(littleEndian: $0.loadUnaligned(as: UInt64.self))
    }
}

struct ReleaseRecord {
    let bytes: Data
    var id: Data { digest(bytes) }
    var sequence: UInt64 { word(bytes, 16) }
    var action: UInt64 { word(bytes, 24) }
    var parent: Data { bytes.subdata(in: 32..<64) }
    var provenance: Data { bytes.subdata(in: 64..<192) }
    var artifact: Data { bytes.subdata(in: 64..<96) }
    var target: Data { bytes.subdata(in: 192..<224) }
    var targetSequence: UInt64 { word(bytes, 224) }
    var artifactSize: UInt64 { word(bytes, 232) }

    init(_ raw: Data, publisher: Data) throws {
        try require(raw.count >= 304 && raw.count <= recordLimit, "invalid release record length")
        try require(raw.prefix(8) == Data("RF2REL01".utf8) && word(raw, 8) == 1,
                    "unsupported release record")
        try require(word(raw, 288) == UInt64(raw.count - 296), "invalid release signature length")
        try require((1...32).contains(word(raw, 16)) && [1, 2].contains(word(raw, 24)),
                    "invalid release sequence or action")
        try require(word(raw, 232) > 0 && word(raw, 232) <= UInt64(maxArtifact) &&
                    word(raw, 240) == 1 && word(raw, 248) == 1,
                    "unsupported release artifact, platform or ABI")
        try require(raw[256..<288] == digest(publisher), "release publisher does not match enrolled key")
        let key = try P256.Signing.PublicKey(x963Representation: publisher)
        let signature = try P256.Signing.ECDSASignature(derRepresentation: raw.dropFirst(296))
        var message = Data("RF2 release chain signature v1".utf8)
        message.append(contentsOf: [0, 0])
        message.append(raw.prefix(288))
        try require(key.isValidSignature(signature, for: message), "invalid release signature")
        self.bytes = raw
    }
}

struct ReleaseHistory {
    private static let zero = Data(repeating: 0, count: 32)
    private let publisher: Data
    private var records: [ReleaseRecord] = []
    private var body = Data()
    private var selected: UInt64 = 0
    var head: Data { records.last?.id ?? Self.zero }

    init(publisher: Data) {
        self.publisher = publisher
    }

    private mutating func accept(_ record: ReleaseRecord, artifact: Data) throws {
        try require(record.sequence == UInt64(records.count + 1) && record.parent == head,
                    "record does not extend current release history")
        try require(record.artifactSize == UInt64(artifact.count) && digest(artifact) == record.artifact,
                    "artifact differs from signed release")
        if record.action == 1 {
            try require(record.target == Self.zero && record.targetSequence == 0, "unexpected rollback target")
            selected = record.sequence
        } else {
            try require(record.targetSequence > 0 && record.targetSequence <= UInt64(records.count),
                        "rollback target was never accepted")
            let target = records[Int(record.targetSequence - 1)]
            try require(target.action == 1 && target.id == record.target &&
                        target.provenance == record.provenance && target.artifactSize == record.artifactSize,
                        "rollback target payload differs from its original release")
            selected = target.sequence
        }
        let entrySize = 16 + record.bytes.count + artifact.count
        try require(entrySize <= stateLimit - 64 - body.count, "release state exceeds format size limit")
        body.append(word(UInt64(record.bytes.count)))
        body.append(record.bytes)
        body.append(word(UInt64(artifact.count)))
        body.append(artifact)
        records.append(record)
    }

    mutating func accept(_ raw: Data, artifact: Data) throws {
        try accept(ReleaseRecord(raw, publisher: publisher), artifact: artifact)
    }

    init(publisher: Data, state: Data, checkpoint: Data) throws {
        self.init(publisher: publisher)
        try require((64...stateLimit).contains(state.count) && state.prefix(8) == Data("RF2CHN01".utf8),
                    "invalid release state")
        let count = word(state, 8)
        try require(count <= 32, "release history exceeds record limit")
        var offset = 64
        func next(_ bufferLimit: Int) throws -> Data {
            try require(state.count - offset >= 8, "truncated release state")
            let length = word(state, offset)
            offset += 8
            try require(length <= UInt64(min(bufferLimit, state.count - offset)), "invalid state entry length")
            defer { offset += Int(length) }
            return state.subdata(in: offset..<offset + Int(length))
        }
        for _ in 0..<count {
            let raw = try next(recordLimit)
            let artifact = try next(maxArtifact)
            try accept(raw, artifact: artifact)
        }
        try require(offset == state.count && word(state, 16) == count &&
                    word(state, 24) == selected && state[32..<64] == head,
                    "release state header differs from decoded history")
        try require(checkpoint == self.checkpoint, "trusted checkpoint differs from release history")
    }

    var state: Data {
        let count = word(UInt64(records.count))
        return Data("RF2CHN01".utf8) + count + count + word(selected) + head + body
    }

    var checkpoint: Data {
        Data("RF2PIN01".utf8) + digest(publisher) + word(UInt64(records.count)) + head
    }
}
